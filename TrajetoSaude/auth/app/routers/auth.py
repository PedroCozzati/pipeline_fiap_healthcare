import re
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Usuario
from app.schemas import LoginRequest, RegistroRequest, TokenResponse, UsuarioResponse
from app.services.auth_service import authenticate_user, create_token, decode_token, register_user

router = APIRouter()
bearer = HTTPBearer()


@router.post("/register", response_model=UsuarioResponse, status_code=201)
def register(payload: RegistroRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, payload.nome, payload.email, payload.senha, payload.tipo)
        return user
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.senha)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas.")
    token = create_token({"sub": str(user.id), "tipo": user.tipo, "nome": user.nome})
    return TokenResponse(
        access_token=token,
        tipo=user.tipo,
        usuario_id=str(user.id),
        nome=user.nome,
    )


@router.get("/me", response_model=UsuarioResponse)
def me(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_token(credentials.credentials)
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")

    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user


class CorenValidateRequest(BaseModel):
    numero: str


@router.post("/validate-coren")
async def validate_coren(payload: CorenValidateRequest):
    """
    Valida CPF ou número COREN-SP.
    - '000.000.000-00' é sempre aceito como mock.
    - Se INFOSIMPLES_TOKEN configurado, consulta a API real.
    - Caso contrário, valida apenas o formato.
    """
    numero = payload.numero.strip()

    # Mock universal
    if numero == "000.000.000-00":
        return {"valid": True, "nome": "Profissional Mock", "situacao": "Ativo (mock)"}

    # Validação de formato CPF (XXX.XXX.XXX-XX)
    cpf_pattern = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
    coren_pattern = re.compile(r"^\d{4,8}(-[A-Z]{2})?$", re.IGNORECASE)

    if not cpf_pattern.match(numero) and not coren_pattern.match(numero):
        return {"valid": False, "nome": None, "situacao": "Formato inválido. Use XXX.XXX.XXX-XX (CPF) ou número COREN."}

    # Validação via infosimples (se token configurado)
    if settings.infosimples_token:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.infosimples.com/api/v2/consultas/coren-sp/cadastro",
                    json={"token": settings.infosimples_token, "cpf": numero},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    registros = data.get("data", [])
                    if registros:
                        r = registros[0]
                        return {
                            "valid": True,
                            "nome": r.get("nome"),
                            "situacao": r.get("situacao"),
                        }
                    return {"valid": False, "nome": None, "situacao": "Profissional não encontrado no COREN-SP."}
        except Exception:
            pass  # fallback para validação de formato

    # Fallback: formato válido → aceita
    return {"valid": True, "nome": None, "situacao": "Formato válido (validação offline)"}


@router.post("/verify")
def verify(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    try:
        payload = decode_token(credentials.credentials)
        return {
            "valid": True,
            "sub": payload.get("sub"),
            "tipo": payload.get("tipo"),
            "nome": payload.get("nome"),
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado.")
