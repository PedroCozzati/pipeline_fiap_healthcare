import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any

from TrajetoSaude.sentinel_ai.app.routers.sentinel import _STREAM_URL_PACIENTE
import httpx
from google import auth as google_auth
from google.auth.transport import requests as google_requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .ingest import (
    load_ubs_points,
    parse_location_string,
    find_nearest_ubs,
    find_ubs_along_route,
)
from .model import DEFAULT_FEATURE_COLUMNS, load_model, predict_risk

logger = logging.getLogger("trajeto_api")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Trajeto Saúde — API",
    description="Predição de risco, UBS mais próxima e proxy Sentinel.AI (GCP).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4000", "http://localhost:4200", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Paths & endpoints ─────────────────────────────────────────────────────────
_BASE = Path(__file__).resolve().parents[1]
MODEL_PATH       = _BASE / "artefatos" / "risk_model.joblib"
UBS_GEOJSON_PATH = _BASE / "raw" / "gis" / "geoportal_equipamento_saude_ubs_posto_centro_v2.geojson"

_RE_BASE    = (
    "https://us-west1-aiplatform.googleapis.com/v1"
    "/projects/traj-saude/locations/us-west1"
    "/reasoningEngines/4633016544006242304"
)

# ── Schemas ───────────────────────────────────────────────────────────────────
class RiskInput(BaseModel):
    Idade: float
    Tempo_Deslocamento_Min: float
    Qtd_UBS_Origem_3km: float
    Glicemia_Aferida: float


class SentinelInput(BaseModel):
    input: str


class SentinelRequest(BaseModel):
    input: SentinelInput


# ── Auth helper ───────────────────────────────────────────────────────────────
def _get_token() -> str:
    credentials, _ = google_auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(google_requests.Request())
    return credentials.token


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
def load_resources():
    try:
        app.state.model = load_model(MODEL_PATH)
        logger.info("Modelo carregado: %s", MODEL_PATH)
    except Exception as exc:
        raise RuntimeError(f"Não foi possível carregar o modelo: {exc}") from exc

    try:
        app.state.ubs_df = load_ubs_points(UBS_GEOJSON_PATH)
        logger.info("UBS carregadas: %d pontos", len(app.state.ubs_df))
    except Exception as exc:
        raise RuntimeError(f"Não foi possível carregar os dados de UBS: {exc}") from exc


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok", "model_path": str(MODEL_PATH)}


# ── Risk prediction ───────────────────────────────────────────────────────────
@app.post("/predict")
def predict(payload: RiskInput) -> Dict[str, Any]:
    model = getattr(app.state, "model", None)
    if model is None:
        raise HTTPException(status_code=500, detail="Modelo não foi carregado")
    return predict_risk(model, payload.dict())


@app.get("/features")
def features():
    return {"feature_columns": DEFAULT_FEATURE_COLUMNS}


# ── Nearest UBS ───────────────────────────────────────────────────────────────
@app.get("/nearest_ubs")
def nearest_ubs(
    current_location: str,
    work_location: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
) -> Dict[str, object]:
    ubs_df = getattr(app.state, "ubs_df", None)
    if ubs_df is None or ubs_df.empty:
        raise HTTPException(status_code=500, detail="Dados das UBS não foram carregados")

    current = parse_location_string(current_location, ubs_df)
    if current is None:
        raise HTTPException(status_code=400, detail=f"Localização '{current_location}' não pôde ser resolvida")

    nearest = find_nearest_ubs(current["latitude"], current["longitude"], ubs_df, limit)
    response: Dict[str, Any] = {
        "current_location": current,
        "nearest_ubs": [
            {
                "nm_equipamento": row["nm_equipamento"],
                "tx_endereco_equipamento": row["tx_endereco_equipamento"],
                "nm_bairro_equipamento": row["nm_bairro_equipamento"],
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "distance_km": float(row["distance_km"]),
            }
            for _, row in nearest.iterrows()
        ],
    }

    if work_location:
        work = parse_location_string(work_location, ubs_df)
        if work is None:
            raise HTTPException(status_code=400, detail=f"Localização de trabalho '{work_location}' não pôde ser resolvida")
        route_candidates = find_ubs_along_route(current, work, ubs_df, limit)
        response["work_location"] = work
        response["route_ubs"] = [
            {
                "nm_equipamento": row["nm_equipamento"],
                "tx_endereco_equipamento": row["tx_endereco_equipamento"],
                "nm_bairro_equipamento": row["nm_bairro_equipamento"],
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "distance_to_current_km": float(row["distance_to_current_km"]),
                "distance_to_work_km": float(row["distance_to_work_km"]),
                "route_score": float(row["route_score"]),
            }
            for _, row in route_candidates.iterrows()
        ]

    return response


# ── Sentinel.AI ───────────────────────────────────────────────────────────────
@app.post("/sentinel/query")
async def sentinel_query(payload: SentinelRequest):
    """
    Proxy para o Vertex AI ADK Agent Engine via HTTP (sem SDK).
    Fluxo: autenticar → criar sessão → streamQuery (SSE) → coletar texto.
    """

    try:
        token = _get_token()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ADC. Execute: gcloud auth application-default login. ({exc})",
        )

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {token}",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        # streamQuery direto — sem sessão (agente stateless)
        print(payload.model_dump())
        
        partes: list[str] = []
        async with client.post(
            _STREAM_URL_PACIENTE,
            headers=headers,
            json=payload.model_dump(),
        ) as stream_resp:
            if stream_resp.status_code != 200:
                body = await stream_resp.aread()
                logger.error("GCP streamQuery erro %s: %s", stream_resp.status_code, body.decode()[:500])
                raise HTTPException(status_code=stream_resp.status_code, detail=body.decode())

            async for line in stream_resp.aiter_lines():
                line = line.strip()
                if not line:
                    continue

                # Suporta SSE (data: {...}) e NDJSON puro
                raw = line[5:].strip() if line.startswith("data:") else line
                if not raw or raw == "[DONE]":
                    continue

                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                author  = event.get("author", "")
                content = event.get("content") or {}

                for part in content.get("parts", []):
                    # Ignora function_call / function_response / thought_signature
                    if "function_call" in part or "function_response" in part:
                        continue
                    texto = part.get("text", "")
                    if texto and author != "user":
                        partes.append(texto)

    resposta = "".join(partes)
    logger.info("Sentinel (%d chars): %s…", len(resposta), resposta[:100])
    return {"output": resposta}
