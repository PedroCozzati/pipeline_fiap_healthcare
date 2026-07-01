from fastapi import FastAPI

from app.database import Base
from app.services.cloud_sql import get_engine
from app.routers import storage
from app.routers.pacientes import router as pacientes_router
from app.routers.agentes import router as agentes_router
from app.routers.triagens import router as triagens_router
from app.routers.tickets import router as tickets_router

# Cria tabelas na inicialização
try:
    Base.metadata.create_all(bind=get_engine())
except Exception as exc:
    import logging
    logging.getLogger("storage_ms").warning("DB indisponível no startup: %s", exc)

api = FastAPI(
    title="Trajeto Saúde — Storage MS",
    description="Microserviço de armazenamento: GCS, Cloud SQL, pacientes, triagens e tickets.",
    version="1.0.0",
)

api.include_router(storage.router, prefix="/storage", tags=["GCS / SQL raw"])
api.include_router(pacientes_router, prefix="/pacientes", tags=["Pacientes"])
api.include_router(agentes_router, prefix="/agentes", tags=["Agentes de Saúde"])
api.include_router(triagens_router, prefix="/triagens", tags=["Triagens"])
api.include_router(tickets_router, prefix="/tickets", tags=["Tickets"])


@api.get("/health", tags=["infra"])
def health():
    from app.config import PROJECT_ROOT, settings
    import os
    from pathlib import Path

    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    return {
        "status": "ok",
        "service": "storage",
        "project_root": str(PROJECT_ROOT),
        "gcs_bucket": settings.gcs_bucket_name,
        "credentials_loaded": bool(creds_path and Path(creds_path).exists()),
    }
