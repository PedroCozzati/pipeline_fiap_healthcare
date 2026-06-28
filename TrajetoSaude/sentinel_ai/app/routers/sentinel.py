import httpx
from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas.sentinel import SentinelRequest, SentinelResponse
from app.services import gcp_auth

router = APIRouter()


@router.post("/query", response_model=SentinelResponse, summary="Consulta ao agente Sentinel.AI (GCP Reasoning Engine)")
async def query_sentinel(payload: SentinelRequest):
    """
    Proxy autenticado para o Vertex AI Reasoning Engine.
    O token ADC é gerenciado pelo servidor — nenhuma credencial fica no browser.
    """
    try:
        token = gcp_auth.get_access_token()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao obter token GCP (ADC). Execute: gcloud auth application-default login. Detalhe: {exc}",
        )

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            settings.gcp_reasoning_engine_url,
            json=payload.model_dump(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()
