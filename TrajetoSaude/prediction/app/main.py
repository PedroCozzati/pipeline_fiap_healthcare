import logging

from fastapi import FastAPI, Request

from app.routers import ingest, predict
from app.services.model_loader import load_model

logger = logging.getLogger("prediction_ms")

api = FastAPI(
     title="Trajeto Saúde — Prediction MS",
     description="Microserviço de predição de risco com modelo local ou GCS.",
     version="1.0.0",
)

api.include_router(predict.router, prefix="/predict", tags=["Predição"])
api.include_router(ingest.router, prefix="/ingest", tags=["Ingestão"])


@api.on_event("startup")
def startup():
     try:
          api.state.model = load_model()
          logger.info("Modelo carregado com sucesso.")
     except Exception as exc:
          logger.warning("Modelo não carregado no startup: %s", exc)
          api.state.model = None


@api.get("/health", tags=["infra"])
def health(request: Request):
     from app.config import resolve_model_path, settings
     import os

     model_loaded = getattr(request.app.state, "model", None) is not None
     model_path = None
     if model_loaded:
          try:
               model_path = str(resolve_model_path())
          except FileNotFoundError:
               pass

     return {
          "status": "ok",
          "service": "prediction",
          "model_loaded": model_loaded,
          "model_source": settings.model_source,
          "model_path": model_path,
          "credentials_loaded": bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")),
     }
