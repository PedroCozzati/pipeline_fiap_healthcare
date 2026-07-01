import logging

from fastapi import APIRouter, HTTPException, Request

from app.pipeline.runner import run_ingestion_pipeline
from app.services.model_loader import load_model

logger = logging.getLogger("prediction_ms")

router = APIRouter()


@router.post("/run")
def run_ingest(request: Request):
     """Executa o pipeline de descoberta, treina o modelo e envia artefatos ao GCS via storage MS."""
     try:
          result = run_ingestion_pipeline()
     except FileNotFoundError as exc:
          raise HTTPException(status_code=422, detail=str(exc)) from exc
     except RuntimeError as exc:
          raise HTTPException(status_code=502, detail=str(exc)) from exc
     except Exception as exc:
          logger.exception("Falha no pipeline de ingestão")
          raise HTTPException(status_code=500, detail=str(exc)) from exc

     try:
          request.app.state.model = load_model()
          result["model_reloaded"] = True
     except Exception as exc:
          logger.warning("Artefatos enviados, mas modelo não recarregado: %s", exc)
          result["model_reloaded"] = False
          result["model_reload_error"] = str(exc)

     return result
