import json
import logging

import httpx
from fastapi import APIRouter, HTTPException

from app.config import resolve_reasoning_engine_url, settings
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


def _extract_text_response(data: dict) -> str:
    if isinstance(data, str):
        return data
    if not isinstance(data, dict):
        return json.dumps(data)

    if "output" in data and isinstance(data["output"], str):
        return data["output"]
    if "response" in data:
        response = data["response"]
        if isinstance(response, dict):
            if "output" in response and isinstance(response["output"], str):
                return response["output"]
            if "content" in response and isinstance(response["content"], str):
                return response["content"]
    if "content" in data and isinstance(data["content"], str):
        return data["content"]
    return json.dumps(data)


async def _query_reasoning_engine(
    mensagem: str,
    user_id: str = "user",
    *,
    agente: bool = False,
) -> str:
    query_url = resolve_reasoning_engine_url(agente=agente)
    headers = _auth_headers()
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            query_url,
            headers=headers,
            json={
                "class_method": "query",
                "input": {
                    "user_id": user_id,
                    "message": mensagem,
                },
            },
        )

    if resp.status_code != 200:
        detail = resp.text
        logger.error("GCP query erro %s: %s", resp.status_code, detail[:500])
        raise HTTPException(status_code=resp.status_code, detail=detail)

    try:
        payload = resp.json()
        return _extract_text_response(payload)
    except json.JSONDecodeError:
        return resp.text


# ── Endpoint legado ────────────────────────────────────────────────────────────

@router.post(
    "/query",
    response_model=SentinelResponse,
    summary="Consulta genérica ao Sentinel.AI",
)
async def query_sentinel(payload: SentinelRequest):
    resposta = await _query_reasoning_engine(payload.input.input)
    return {"output": resposta}


# ── sentinelai_paciente ────────────────────────────────────────────────────────

@router.post(
    "/sentinelai_paciente",
    response_model=SentinelAgentePacienteResponse,
    summary="Chatbot Sentinel.AI — orientação ao paciente",
)
async def sentinelai_paciente(payload: SentinelPacienteRequest):
    """
    Enriquece a mensagem com dados do paciente e localização, e consulta o Reasoning Engine.
    """
    partes: list[str] = [
        "Você é um assistente de saúde que orienta pacientes sobre suas rotas e atendimentos.",
        "Use os dados do paciente para responder de forma clara e objetiva.",
        "",
        "Dados do paciente:",
    ]

    if payload.nome_paciente:
        partes.append(f"- Nome: {payload.nome_paciente}")
    if payload.endereco_paciente:
        partes.append(f"- Endereço residencial: {payload.endereco_paciente}")
    if payload.localizacao:
        loc = payload.localizacao
        if loc.bairro:
            partes.append(f"- Bairro: {loc.bairro}")
        if loc.cidade:
            partes.append(f"- Cidade: {loc.cidade}")
        if loc.local_trabalho:
            partes.append(f"- Local de trabalho: {loc.local_trabalho}")
        if loc.rota_trabalho:
            partes.append(f"- Rota de trabalho: {' → '.join(loc.rota_trabalho)}")
    if payload.carteira_sus:
        partes.append(f"- CNS: {payload.carteira_sus}")

    partes += ["", f"Pergunta do paciente: {payload.mensagem}"]

    input_text = "\n".join(partes)
    user_id = payload.carteira_sus or "paciente"
    resposta = await _query_reasoning_engine(input_text, user_id=user_id)
    logger.info("sentinelai_paciente (%d chars)", len(resposta))
    return {"output": resposta, "contexto_enviado": input_text}


# ── sentinelai_agente ──────────────────────────────────────────────────────────

@router.post(
    "/sentinelai_agente",
    response_model=SentinelAgenteResponse,
    summary="Sentinel.AI — UBS mais próximas da rota do paciente",
)
async def sentinelai_agente(payload: SentinelAgenteRequest):
    """
    Recebe dados do paciente e localização do hub de atendimento, e retorna UBS recomendadas.
    """
    partes: list[str] = [
        "Você é um assistente de logística de saúde pública.",
        "Com base nos dados abaixo, liste as UBS mais indicadas para o paciente, considerando o endereço de atendimento e a rota de trabalho.",
        "Responda APENAS com um JSON válido do formato solicitado, sem texto adicional.",
        "",
        "Dados do paciente:",
    ]

    if payload.nome_paciente:
        partes.append(f"- Nome: {payload.nome_paciente}")
    if payload.endereco_paciente:
        partes.append(f"- Endereço residencial: {payload.endereco_paciente}")
    if payload.local_trabalho:
        partes.append(f"- Local de trabalho: {payload.local_trabalho}")
    if payload.rota_trabalho:
        partes.append(f"- Rota de trabalho: {' → '.join(payload.rota_trabalho)}")

    partes += [
        "",
        "Endereço do hub onde está acontecendo o atendimento:",
        f"- Endereço: {payload.endereco_hub}",
    ]
    if payload.lat_hub is not None and payload.lng_hub is not None:
        partes.append(f"- Coordenadas GPS: {payload.lat_hub}, {payload.lng_hub}")

    partes += [
        "",
        "Formato de saída esperado:",
        '{"items":[{"name":"...","description":"...","address":"...","cep":"..."}]}'
    ]

    input_text = "\n".join(partes)
    resposta_raw = await _query_reasoning_engine(input_text, user_id="agente", agente=True)
    logger.info("sentinelai_agente raw (%d chars): %s", len(resposta_raw), resposta_raw[:200])

    items: list[UbsRecomendada] = []
    try:
        inicio = resposta_raw.find("{")
        fim = resposta_raw.rfind("}") + 1
        if inicio >= 0 and fim > inicio:
            dados = json.loads(resposta_raw[inicio:fim])
            items = [UbsRecomendada(**i) for i in dados.get("items", []) if isinstance(i, dict)]
    except Exception as exc:
        logger.warning("Falha ao parsear JSON do agente: %s — raw: %s", exc, resposta_raw[:300])

    return SentinelAgenteResponse(items=items, output_raw=resposta_raw)
