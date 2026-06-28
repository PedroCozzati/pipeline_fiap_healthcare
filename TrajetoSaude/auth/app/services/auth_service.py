from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Usuario

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def register_user(db: Session, nome: str, email: str, senha: str, tipo: str) -> Usuario:
    if db.query(Usuario).filter(Usuario.email == email).first():
        raise ValueError("Email já cadastrado.")
    user = Usuario(nome=nome, email=email, senha_hash=hash_password(senha), tipo=tipo)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, senha: str) -> Usuario | None:
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user or not verify_password(senha, user.senha_hash):
        return None
    return user
