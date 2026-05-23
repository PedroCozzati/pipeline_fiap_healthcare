from pathlib import Path
from typing import Dict, Optional, Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from ingest import (
    load_ubs_points,
    parse_location_string,
    find_nearest_ubs,
    find_ubs_along_route,
)
from model import DEFAULT_FEATURE_COLUMNS, load_model, predict_risk

app = FastAPI(
    title="Risk Model API",
    description="API para previsão de risco usando o modelo treinado pela pipeline.",
    version="0.1.0",
)

MODEL_PATH = Path(__file__).resolve().parents[1] / "output" / "risk_model.joblib"
UBS_GEOJSON_PATH = Path(__file__).resolve().parents[1] / "raw" / "gis" / "geoportal_equipamento_saude_ubs_posto_centro_v2.geojson"


class RiskInput(BaseModel):
    Idade: float
    Tempo_Deslocamento_Min: float
    Qtd_UBS_Origem_3km: float
    Glicemia_Aferida: float


@app.on_event("startup")
def load_trained_model():
    try:
        app.state.model = load_model(MODEL_PATH)
    except Exception as exc:
        raise RuntimeError(f"Não foi possível carregar o modelo: {exc}") from exc

    try:
        app.state.ubs_df = load_ubs_points(UBS_GEOJSON_PATH)
    except Exception as exc:
        raise RuntimeError(f"Não foi possível carregar os dados de UBS: {exc}") from exc


@app.get("/health")
def health_check():
    return {"status": "ok", "model_path": str(MODEL_PATH)}


@app.post("/predict")
def predict(payload: RiskInput) -> Dict[str, Any]:
    model = getattr(app.state, "model", None)
    if model is None:
        raise HTTPException(status_code=500, detail="Modelo não foi carregado")

    result = predict_risk(model, payload.dict())
    return result


@app.get("/features")
def features():
    return {"feature_columns": DEFAULT_FEATURE_COLUMNS}


@app.get("/nearest_ubs")
def nearest_ubs(
    current_location: str,
    work_location: Optional[str] = None,
    limit: int = Query(5, ge=1, le=20),
) -> Dict[str, object]:
    """Return the nearest UBS locations to the current location and optionally along the route to work.

    Args:
        current_location: Current location name or latitude,longitude coordinates.
        work_location: Optional work location name or latitude,longitude coordinates.
        limit: Maximum number of UBS results to return.

    Returns:
        A JSON object containing the current location resolution, nearest UBS, and
        route-aware UBS recommendations when work_location is provided.
    """
    ubs_df = getattr(app.state, "ubs_df", None)
    if ubs_df is None or ubs_df.empty:
        raise HTTPException(status_code=500, detail="Dados das UBS não foram carregados")

    current = parse_location_string(current_location, ubs_df)
    if current is None:
        raise HTTPException(status_code=400, detail=f"Localização atual '{current_location}' não pôde ser resolvida")

    nearest = find_nearest_ubs(current["latitude"], current["longitude"], ubs_df, limit)
    response = {
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

#TODO AJUSTAR ENDPOINT DE LOCALIZAÇÂO DE UBS MAIS PROXIMA