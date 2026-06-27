from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import sentinel, risk, hubs

api = FastAPI(
    title="Trajeto Saúde — API",
    description="Backend para o agente Sentinel.AI, predição de risco e indicação de hubs/UBS.",
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
api.include_router(risk.router,     prefix="/risk",     tags=["Predição de Risco"])
api.include_router(hubs.router,     prefix="/hubs",     tags=["Hubs / UBS"])


@api.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "service": "trajeto-api", "version": "1.0.0"}
