from typing import Optional
from pydantic import BaseModel


class SentinelInput(BaseModel):
    input: str


class SentinelRequest(BaseModel):
    input: SentinelInput


class SentinelResponse(BaseModel):
    output: str | dict | None = None


# ── Endpoint: sentinelai_paciente ─────────────────────────────────────────────

class SentinelPacienteRequest(BaseModel):
    mensagem: str
    nome_paciente: Optional[str] = None
    carteira_sus: Optional[str] = None
    endereco_atual: Optional[str] = None
    endereco_casa: Optional[str] = None
    local_trabalho: Optional[str] = None
    rota_trabalho: Optional[list[str]] = None


# ── Endpoint: sentinelai_agente ───────────────────────────────────────────────

class SentinelAgenteRequest(BaseModel):
    localizacao_atual: str
    rota_trabalho: Optional[list[str]] = None
    local_trabalho: Optional[str] = None
    endereco_casa: Optional[str] = None


class UbsRecomendada(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    cep: Optional[str] = None


class SentinelAgenteResponse(BaseModel):
    items: list[UbsRecomendada]
    output_raw: Optional[str] = None

    model_config = {"extra": "ignore"}


class SentinelAgentePacienteResponse(BaseModel):
    output: str | dict | None = None
    contexto_enviado: Optional[str] = None

    model_config = {"extra": "ignore"}
