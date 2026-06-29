from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.clients.services import storage_client, prediction_client, auth_client, sentinel_client
from app.routers import storage, prediction, auth
from app.routers.seed import router as seed_router
from app.routers.sentinel import router as sentinel_router

api = FastAPI(
     title="Trajeto Saúde — API Gateway",
     description="Gateway que agrega os microserviços de armazenamento, predição e Sentinel.AI.",
     version="1.0.0",
)

api.add_middleware(
     CORSMiddleware,
     allow_origins=settings.cors_origins,
     allow_credentials=True,
     allow_methods=["*"],
     allow_headers=["*"],
)

api.include_router(auth.router, prefix="/api/auth", tags=["Autenticação"])
api.include_router(storage.router, prefix="/api/storage", tags=["Armazenamento"])
api.include_router(prediction.router, prefix="/api/prediction", tags=["Predição"])
api.include_router(sentinel_router, prefix="/api/sentinel", tags=["Sentinel"])
api.include_router(seed_router, prefix="/api/seed", tags=["Seed"])


@api.get("/health", tags=["infra"])
async def health():
     details: dict = {}
     ok_flags = []

     for name, client in [("auth", auth_client), ("storage", storage_client), ("prediction", prediction_client), ("sentinel", sentinel_client)]:
          try:
               h = await client.health()
               ok_flags.append(h.get("status") == "ok")
               details[name] = h
          except Exception as exc:
               ok_flags.append(False)
               details[name] = {"status": "error", "detail": str(exc)}

     return {
          "status": "ok" if all(ok_flags) else "degraded",
          "service": "gateway",
          "dependencies": details,
     }
