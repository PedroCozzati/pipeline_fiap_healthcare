from fastapi import APIRouter, Request

from app.clients.services import sentinel_client

router = APIRouter()

@router.post("/query", summary="Consulta a Sentinel.AI")
async def query_sentinel(request: Request):
    return await sentinel_client.post("/sentinel/query", json=await request.json())


@router.post("/sentinelai_paciente", summary="Consulta Sentinel.AI paciente")
async def sentinelai_paciente(request: Request):
    return await sentinel_client.post("/sentinel/sentinelai_paciente", json=await request.json())


@router.post("/sentinelai_agente", summary="Consulta Sentinel.AI agente")
async def sentinelai_agente(request: Request):
    return await sentinel_client.post("/sentinel/sentinelai_agente", json=await request.json())
