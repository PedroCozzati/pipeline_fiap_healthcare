"""
POST /api/seed  —  insere dados de demonstração no banco.
Idempotente: ignora conflitos de e-mail / carteira_sus já existentes.
"""
import json
import httpx
from fastapi import APIRouter
from app.config import settings

router = APIRouter()

AUTH_BASE    = settings.auth_service_url
STORAGE_BASE = settings.storage_service_url

DEMO_USUARIOS = [
    {
        "nome": "Camila Rocha",
        "email": "agente@demo.trajeto",
        "senha": "123456",
        "tipo": "agente_saude",
        "perfil": {
            "registro_profissional": "COREN-SP 123456",
            "especialidade": "Agente Comunitária de Saúde",
            "ubs_vinculada": "UBS Jaraguá",
        },
    },
    {
        "nome": "Maria Souza",
        "email": "paciente@demo.trajeto",
        "senha": "123456",
        "tipo": "paciente",
        "perfil": {
            "carteira_sus": "700123456789012",
            "data_nascimento": "1973-06-15",
            "endereco": "Rua das Flores, 45",
            "cidade": "Jaraguá",
            "estado": "SP",
            "cep": "02900-000",
            "local_trabalho": "Av. Paulista, 1000 — Centro",
            "rota_trabalho": json.dumps(["Jaraguá", "Vila Esperança", "Centro"]),
        },
    },
    {
        "nome": "João Pereira",
        "email": "joao@demo.trajeto",
        "senha": "123456",
        "tipo": "paciente",
        "perfil": {
            "carteira_sus": "700987654321098",
            "data_nascimento": "1987-03-22",
            "endereco": "Rua Voluntários da Pátria, 200",
            "cidade": "Santana",
            "estado": "SP",
            "cep": "02010-000",
            "local_trabalho": "Rua da Consolação, 500 — Centro",
            "rota_trabalho": json.dumps(["Santana", "Centro"]),
        },
    },
]


async def _registrar_ou_buscar_id(client: httpx.AsyncClient, usuario: dict) -> str | None:
    """Registra o usuário e retorna o ID. Se já existe, faz login para obter o ID."""
    # Tenta registrar
    r = await client.post(f"{AUTH_BASE}/auth/register", json={
        "nome": usuario["nome"],
        "email": usuario["email"],
        "senha": usuario["senha"],
        "tipo": usuario["tipo"],
    })

    if r.status_code == 201:
        return r.json().get("id")

    if r.status_code == 409:
        # Usuário já existe — faz login para obter ID
        login = await client.post(f"{AUTH_BASE}/auth/login", json={
            "email": usuario["email"],
            "senha": usuario["senha"],
        })
        if login.status_code == 200:
            return login.json().get("usuario_id")

        # Login falhou — tenta recriar apagando o usuário (não implementado) ou reporta erro
        return None

    return None


async def _criar_perfil(client: httpx.AsyncClient, tipo: str, usuario_id: str, nome: str, perfil: dict) -> dict:
    """Cria perfil no storage. Ignora 409 (já existe)."""
    if tipo == "agente_saude":
        r = await client.post(f"{STORAGE_BASE}/agentes", json={
            "usuario_id": usuario_id, "nome": nome, **perfil
        })
    else:
        r = await client.post(f"{STORAGE_BASE}/pacientes", json={
            "usuario_id": usuario_id, "nome": nome, **perfil
        })

    if r.status_code in (200, 201):
        return {"status": "criado"}
    if r.status_code == 409:
        return {"status": "perfil_já_existia"}
    return {"status": f"erro_storage_{r.status_code}", "detalhe": r.text[:200]}


@router.post("")
async def seed():
    resultados = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for usuario in DEMO_USUARIOS:
            entrada = {"email": usuario["email"], "tipo": usuario["tipo"]}

            usuario_id = await _registrar_ou_buscar_id(client, usuario)
            if not usuario_id:
                resultados.append({**entrada, "status": "erro: não foi possível obter usuario_id"})
                continue

            perfil_result = await _criar_perfil(
                client, usuario["tipo"], usuario_id, usuario["nome"], usuario["perfil"]
            )
            resultados.append({**entrada, "usuario_id": usuario_id, **perfil_result})

    return {"seed": resultados}
