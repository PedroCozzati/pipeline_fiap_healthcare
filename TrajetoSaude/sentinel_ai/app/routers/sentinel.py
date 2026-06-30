import json
import logging

import httpx
from fastapi import APIRouter, HTTPException

from app.schemas.sentinel import (
    SentinelRequest,
    SentinelResponse,
    SentinelPacienteRequest,
    SentinelAgenteRequest,
    SentinelAgenteResponse,
    UbsRecomendada,
    SentinelAgentePacienteResponse,
)
from app.services import gcp_auth

router = APIRouter()
logger = logging.getLogger("sentinel_ai")

_GCP_BASE = (
    "https://us-west1-aiplatform.googleapis.com/v1"
    "/projects/traj-saude/locations/us-west1/reasoningEngines"
)

_STREAM_URL_PACIENTE = f"{_GCP_BASE}/4633016544006242304:streamQuery"
_STREAM_URL_AGENTE   = f"{_GCP_BASE}/4425112089333334016:streamQuery"


def _auth_headers() -> dict:
    try:
        token = gcp_auth.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao obter token GCP (ADC): {exc}",
        )


async def _stream_query(mensagem: str, stream_url: str) -> str:
    """Chama o Vertex AI Reasoning Engine via streamQuery (SSE) e coleta o texto."""
    headers = _auth_headers()
    partes: list[str] = []

    async with httpx.AsyncClient(timeout=200.0) as client:
        async with client.stream(
            "POST",
            stream_url,
            headers=headers,
            json={
                "class_method": "async_stream_query",
                "input": {
                    "user_id": "user",
                    "message": mensagem,
                },
            },
        ) as resp:
            if resp.status_code != 200:
                body = await resp.aread()
                logger.error("GCP streamQuery erro %s: %s", resp.status_code, body.decode()[:500])
                raise HTTPException(status_code=resp.status_code, detail=body.decode())

            async for line in resp.aiter_lines():
                line = line.strip()
                if not line:
                    continue
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
                    if "function_call" in part or "function_response" in part:
                        continue
                    texto = part.get("text", "")
                    if texto and author != "user":
                        partes.append(texto)

    return "".join(partes)


# ── Endpoint legado ────────────────────────────────────────────────────────────

@router.post("/query", response_model=SentinelResponse, summary="Consulta genérica ao Sentinel.AI")
async def query_sentinel(payload: SentinelRequest):
    resposta = await _stream_query(payload.input.input, _STREAM_URL_PACIENTE)
    return {"output": resposta}


# ── sentinelai_paciente ────────────────────────────────────────────────────────

@router.post(
    "/sentinelai_paciente",
    response_model=SentinelAgentePacienteResponse,
    summary="Chatbot Sentinel.AI — orientação ao paciente",
)
async def sentinelai_paciente(payload: SentinelPacienteRequest):
    partes: list[str] = [
        "Você é um assistente de saúde que orienta pacientes sobre suas rotas e atendimentos.",
        "Use os dados do paciente para responder de forma clara e objetiva.",
        "",
        "Dados do paciente:",
    ]

    if payload.nome_paciente:
        partes.append(f"- Nome: {payload.nome_paciente}")
    if payload.carteira_sus:
        partes.append(f"- CNS: {payload.carteira_sus}")
    if payload.endereco_casa:
        partes.append(f"- Endereço residencial: {payload.endereco_casa}")
    if payload.local_trabalho:
        partes.append(f"- Local de trabalho: {payload.local_trabalho}")
    if payload.rota_trabalho:
        partes.append(f"- Rota de trabalho: {' → '.join(payload.rota_trabalho)}")
    if payload.endereco_atual:
        partes.append(f"- Localização atual: {payload.endereco_atual}")

    partes += ["", f"Pergunta do paciente: {payload.mensagem}"]

    input_text = "\n".join(partes)
    try:
        resposta = await _stream_query(input_text, _STREAM_URL_PACIENTE)
    except HTTPException as exc:
        logger.warning("sentinelai_paciente GCP error %s", exc.status_code)
        return {
            "output": f"Serviço Sentinel.AI temporariamente indisponível (erro {exc.status_code}).",
            "contexto_enviado": input_text,
        }
    logger.info("sentinelai_paciente (%d chars)", len(resposta))
    return {"output": resposta, "contexto_enviado": input_text}


# ── sentinelai_agente ──────────────────────────────────────────────────────────

@router.post(
    "/sentinelai_agente",
    response_model=SentinelAgenteResponse,
    summary="Sentinel.AI — UBS mais próximas da rota do paciente",
)
async def sentinelai_agente(payload: SentinelAgenteRequest):
    partes: list[str] = []

    if payload.endereco_casa:
        partes.append(f"Residência do paciente: {payload.endereco_casa}.")
    if payload.local_trabalho:
        partes.append(f"Local de trabalho: {payload.local_trabalho}.")
    if payload.rota_trabalho:
        partes.append(f"Rota diária: {' → '.join(payload.rota_trabalho)}.")
    partes.append(f"Localização atual: {payload.localizacao_atual}.")

    partes.append(
        "Com base na rota de trabalho e localização acima, indique as 3 UBS mais adequadas "
        "para este paciente em São Paulo, retornando APENAS um JSON no formato: "
        '{"items":[{"name":"...","description":"...","address":"...","cep":"..."}]}'
    )

    input_text = " ".join(partes)

    try:
        resposta_raw = await _stream_query(input_text, _STREAM_URL_AGENTE)
    except HTTPException as exc:
        logger.warning("sentinelai_agente GCP error %s — retornando lista vazia", exc.status_code)
        return SentinelAgenteResponse(items=[], output_raw=exc.detail)

    logger.info("sentinelai_agente raw (%d chars): %s", len(resposta_raw), resposta_raw[:200])

    items: list[UbsRecomendada] = []
    try:
        inicio = resposta_raw.find("{")
        fim = resposta_raw.rfind("}") + 1
        if inicio >= 0 and fim > inicio:
            json_text = resposta_raw[inicio:fim]
            dados = json.loads(json_text)
            if isinstance(dados, dict) and "items" in dados and isinstance(dados["items"], list):
                for i in dados["items"]:
                    if not isinstance(i, dict):
                        continue
                    normalizado = {k.rstrip(":"): v for k, v in i.items()}
                    try:
                        items.append(UbsRecomendada(**normalizado))
                    except Exception:
                        pass
    except json.JSONDecodeError:
        logger.warning("Resposta JSON inválida do agente — raw: %s", resposta_raw[:300])
    except Exception as exc:
        logger.warning("Falha ao parsear JSON do agente: %s — raw: %s", exc, resposta_raw[:300])

    return SentinelAgenteResponse(items=items, output_raw=resposta_raw)