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

    async with httpx.AsyncClient(timeout=60.0) as client:
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
