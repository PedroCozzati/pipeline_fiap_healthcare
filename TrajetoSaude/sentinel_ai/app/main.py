from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import sentinel

api = FastAPI(
    title="Trajeto Saúde — Sentinel.AI",
    description="Proxy autenticado para o Vertex AI Reasoning Engine (GCP).",
    version="1.0.0",
)

api.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(sentinel.router, prefix="/sentinel", tags=["Sentinel.AI"])


@api.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "service": "sentinel-ai", "version": "1.0.0"}
