from fastapi import APIRouter, Request

from app.clients.services import storage_client

router = APIRouter()


# ── GCS / SQL raw ────────────────────────────────────────────────────────────

@router.get("/blobs", summary="Lista objetos no bucket GCS")
async def list_blobs(prefix: str = ""):
    return await storage_client.get("/storage/gcs/list", params={"prefix": prefix})


@router.get("/blobs/{blob_name:path}", summary="Baixa conteúdo de um objeto GCS")
async def download_blob(blob_name: str):
    return await storage_client.get(f"/storage/gcs/download/{blob_name}")


@router.post("/query", summary="Executa consulta SQL no Cloud SQL")
async def run_query(payload: dict):
    return await storage_client.post("/storage/sql/query", json=payload)


# ── Pacientes ─────────────────────────────────────────────────────────────────

@router.post("/pacientes", status_code=201)
async def criar_paciente(request: Request):
    return await storage_client.post("/pacientes", json=await request.json())


@router.get("/pacientes/usuario/{usuario_id}")
async def buscar_paciente_usuario(usuario_id: str):
    return await storage_client.get(f"/pacientes/usuario/{usuario_id}")


@router.get("/pacientes/sus/{carteira_sus}")
async def buscar_paciente_sus(carteira_sus: str):
    return await storage_client.get(f"/pacientes/sus/{carteira_sus}")


@router.get("/pacientes/{paciente_id}")
async def buscar_paciente(paciente_id: str):
    return await storage_client.get(f"/pacientes/{paciente_id}")


@router.patch("/pacientes/{paciente_id}")
async def atualizar_paciente(paciente_id: str, request: Request):
    return await storage_client.patch(f"/pacientes/{paciente_id}", json=await request.json())


# ── Agentes de Saúde ──────────────────────────────────────────────────────────

@router.post("/agentes", status_code=201)
async def criar_agente(request: Request):
    return await storage_client.post("/agentes", json=await request.json())


@router.get("/agentes/{agente_id}")
async def buscar_agente(agente_id: str):
    return await storage_client.get(f"/agentes/{agente_id}")


@router.get("/agentes/usuario/{usuario_id}")
async def buscar_agente_por_usuario(usuario_id: str):
    return await storage_client.get(f"/agentes/usuario/{usuario_id}")


# ── Triagens ──────────────────────────────────────────────────────────────────

@router.post("/triagens", status_code=201)
async def criar_triagem(request: Request):
    return await storage_client.post("/triagens", json=await request.json())


@router.get("/triagens/{triagem_id}")
async def buscar_triagem(triagem_id: str):
    return await storage_client.get(f"/triagens/{triagem_id}")


@router.get("/triagens/paciente/{paciente_id}")
async def historico_triagens(paciente_id: str):
    return await storage_client.get(f"/triagens/paciente/{paciente_id}")


@router.get("/triagens/agente/{agente_id}")
async def historico_triagens_agente(agente_id: str):
    return await storage_client.get(f"/triagens/agente/{agente_id}")


@router.patch("/triagens/{triagem_id}/predicao")
async def atualizar_predicao(triagem_id: str, risco_probabilidade: float, risco_label: int):
    return await storage_client.patch(
        f"/triagens/{triagem_id}/predicao",
        params={"risco_probabilidade": risco_probabilidade, "risco_label": risco_label},
    )


# ── Tickets ───────────────────────────────────────────────────────────────────

@router.post("/tickets", status_code=201)
async def criar_ticket(request: Request):
    return await storage_client.post("/tickets", json=await request.json())


@router.get("/tickets/{ticket_id}")
async def buscar_ticket(ticket_id: str):
    return await storage_client.get(f"/tickets/{ticket_id}")


@router.post("/tickets/{ticket_id}/utilizar")
async def utilizar_ticket(ticket_id: str):
    return await storage_client.post(f"/tickets/{ticket_id}/utilizar")
