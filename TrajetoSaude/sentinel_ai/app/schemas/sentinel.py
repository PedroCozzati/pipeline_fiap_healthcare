from typing import Optional
from pydantic import BaseModel


class SentinelInput(BaseModel):
    input: str


class SentinelRequest(BaseModel):
    input: SentinelInput


class SentinelResponse(BaseModel):
    output: str | dict | None = None


# ── Endpoint: sentinelai_paciente ─────────────────────────────────────────────

class LocalizacaoPaciente(BaseModel):
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    rota_trabalho: Optional[list[str]] = None
    local_trabalho: Optional[str] = None


class SentinelPacienteRequest(BaseModel):
    mensagem: str
    localizacao: Optional[LocalizacaoPaciente] = None
    carteira_sus: Optional[str] = None
    nome_paciente: Optional[str] = None


# ── Endpoint: sentinelai_agente ───────────────────────────────────────────────

class SentinelAgenteRequest(BaseModel):
    """
    Dados do paciente + localização do hub onde está acontecendo o atendimento.
    O agente retorna as UBS mais próximas da rota de trabalho do paciente.
    """
    nome_paciente: Optional[str] = None
    endereco_paciente: Optional[str] = None
    local_trabalho: Optional[str] = None
    rota_trabalho: Optional[list[str]] = None

    # Hub onde está acontecendo o atendimento (GPS do celular/PC)
    endereco_hub: str
    lat_hub: Optional[float] = None
    lng_hub: Optional[float] = None


class UbsRecomendada(BaseModel):
    name: str
    description: Optional[str] = None
    address: str
    cep: Optional[str] = None


class SentinelAgenteResponse(BaseModel):
    items: list[UbsRecomendada]
    output_raw: Optional[str] = None  # resposta bruta do agente


class SentinelAgentePacienteResponse(BaseModel):
    output: str | dict | None = None
    contexto_enviado: Optional[str] = None
