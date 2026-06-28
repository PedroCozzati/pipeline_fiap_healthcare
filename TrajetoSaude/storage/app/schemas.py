import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Paciente ──────────────────────────────────────────────────────────────────

class PacienteCreate(BaseModel):
    usuario_id: str
    nome: str
    carteira_sus: str
    data_nascimento: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    lat_residencia: Optional[float] = None
    lng_residencia: Optional[float] = None
    local_trabalho: Optional[str] = None
    lat_trabalho: Optional[float] = None
    lng_trabalho: Optional[float] = None
    rota_trabalho: Optional[str] = None


class PacienteUpdate(BaseModel):
    nome: Optional[str] = None
    data_nascimento: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    lat_residencia: Optional[float] = None
    lng_residencia: Optional[float] = None
    local_trabalho: Optional[str] = None
    lat_trabalho: Optional[float] = None
    lng_trabalho: Optional[float] = None
    rota_trabalho: Optional[str] = None


class PacienteResponse(BaseModel):
    id: uuid.UUID
    usuario_id: str
    nome: str
    carteira_sus: str
    data_nascimento: Optional[str]
    endereco: Optional[str]
    cidade: Optional[str]
    estado: Optional[str]
    cep: Optional[str]
    lat_residencia: Optional[float]
    lng_residencia: Optional[float]
    local_trabalho: Optional[str]
    lat_trabalho: Optional[float]
    lng_trabalho: Optional[float]
    rota_trabalho: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── AgenteSaude ───────────────────────────────────────────────────────────────

class AgenteCreate(BaseModel):
    usuario_id: str
    nome: str
    registro_profissional: Optional[str] = None
    especialidade: Optional[str] = None
    ubs_vinculada: Optional[str] = None


class AgenteResponse(BaseModel):
    id: uuid.UUID
    usuario_id: str
    nome: str
    registro_profissional: Optional[str]
    especialidade: Optional[str]
    ubs_vinculada: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Triagem ───────────────────────────────────────────────────────────────────

class TriagemCreate(BaseModel):
    paciente_id: uuid.UUID
    agente_id: Optional[uuid.UUID] = None
    glicemia: Optional[float] = None
    pressao_sistolica: Optional[int] = None
    pressao_diastolica: Optional[int] = None
    risco_probabilidade: Optional[float] = None
    risco_label: Optional[int] = None


class TriagemResponse(BaseModel):
    id: uuid.UUID
    paciente_id: uuid.UUID
    agente_id: Optional[uuid.UUID]
    glicemia: Optional[float]
    pressao_sistolica: Optional[int]
    pressao_diastolica: Optional[int]
    risco_probabilidade: Optional[float]
    risco_label: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Ticket ────────────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    paciente_id: uuid.UUID
    triagem_id: uuid.UUID
    ubs_encaminhamento: str


class TicketResponse(BaseModel):
    id: uuid.UUID
    paciente_id: uuid.UUID
    triagem_id: uuid.UUID
    ubs_encaminhamento: str
    status: str
    valido_ate: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
