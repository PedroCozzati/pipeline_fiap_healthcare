from pathlib import Path

from fastapi import FastAPI

from app.routers import storage

api = FastAPI(
     title="Trajeto Saúde — Storage MS",
     description="Microserviço de ingestão e consumo de GCS e Cloud SQL.",
     version="1.0.0",
)

api.include_router(storage.router, prefix="/storage", tags=["Armazenamento"])


@api.get("/health", tags=["infra"])
def health():
     from app.config import PROJECT_ROOT, settings
     import os

     creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
     return {
          "status": "ok",
          "service": "storage",
          "project_root": str(PROJECT_ROOT),
          "gcs_bucket": settings.gcs_bucket_name,
          "credentials_loaded": bool(creds_path and Path(creds_path).exists()),
          "credentials_path": creds_path,
     }
