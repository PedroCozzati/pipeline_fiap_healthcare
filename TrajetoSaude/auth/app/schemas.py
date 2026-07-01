import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr


class RegistroRequest(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    tipo: Literal["paciente", "agente_saude"]


class LoginRequest(BaseModel):
    email: str
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tipo: str
    usuario_id: str
    nome: str


class UsuarioResponse(BaseModel):
    id: uuid.UUID
    nome: str
    email: str
    tipo: str

    model_config = {"from_attributes": True}


class TokenPayload(BaseModel):
    sub: str
    tipo: str
    nome: str
