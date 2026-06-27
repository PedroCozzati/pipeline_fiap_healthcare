from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.clients.services import storage_client, prediction_client
from app.routers import storage, prediction

api = FastAPI(
     title="Trajeto Saúde — API Gateway",
     description="Gateway que agrega os microserviços de armazenamento e predição.",
     version="1.0.0",
)

api.add_middleware(
     CORSMiddleware,
     allow_origins=settings.cors_origins,
     allow_credentials=True,
     allow_methods=["*"],
     allow_headers=["*"],
)

api.include_router(storage.router, prefix="/api/storage", tags=["Armazenamento"])
api.include_router(prediction.router, prefix="/api/prediction", tags=["Predição"])


@api.get("/health", tags=["infra"])
async def health():
     storage_ok = prediction_ok = False
     details: dict = {}

     try:
          storage_health = await storage_client.health()
          storage_ok = storage_health.get("status") == "ok"
          details["storage"] = storage_health
     except Exception as exc:
          details["storage"] = {"status": "error", "detail": str(exc)}

     try:
          prediction_health = await prediction_client.health()
          prediction_ok = prediction_health.get("status") == "ok"
          details["prediction"] = prediction_health
     except Exception as exc:
          details["prediction"] = {"status": "error", "detail": str(exc)}

     overall = "ok" if storage_ok and prediction_ok else "degraded"
     return {
          "status": overall,
          "service": "gateway",
          "dependencies": details,
     }
