from fastapi import APIRouter, Request

from app.clients.services import sentinel_client

router = APIRouter()

_SENTINEL_TIMEOUT = 220.0  # sentinel_ai aguarda até 200s da Vertex AI; gateway precisa de margem extra

@router.post("/query", summary="Consulta a Sentinel.AI")
async def query_sentinel(request: Request):
    return await sentinel_client.post("/sentinel/query", json=await request.json(), timeout=_SENTINEL_TIMEOUT)


@router.post("/sentinelai_paciente", summary="Consulta Sentinel.AI paciente")
async def sentinelai_paciente(request: Request):
    return await sentinel_client.post("/sentinel/sentinelai_paciente", json=await request.json(), timeout=_SENTINEL_TIMEOUT)


@router.post("/sentinelai_agente", summary="Consulta Sentinel.AI agente")
async def sentinelai_agente(request: Request):
    return await sentinel_client.post("/sentinel/sentinelai_agente", json=await request.json(), timeout=_SENTINEL_TIMEOUT)


@router.post("/ubs_raio_casa", summary="UBS em raio de 3km da residência do paciente")
async def ubs_raio_casa(request: Request):
    return await sentinel_client.post("/sentinel/ubs_raio_casa", json=await request.json(), timeout=_SENTINEL_TIMEOUT)
