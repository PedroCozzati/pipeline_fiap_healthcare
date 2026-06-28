from fastapi import FastAPI

from app.database import Base, get_engine
from app.routers.auth import router as auth_router

try:
    Base.metadata.create_all(bind=get_engine())
except Exception as exc:
    import logging
    logging.getLogger("auth_ms").warning("DB indisponível no startup: %s", exc)

api = FastAPI(
    title="Trajeto Saúde — Auth Service",
    description="Autenticação e gerenciamento de usuários (paciente / agente_saude).",
    version="1.0.0",
)

api.include_router(auth_router, prefix="/auth", tags=["Autenticação"])


@api.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "service": "auth"}
