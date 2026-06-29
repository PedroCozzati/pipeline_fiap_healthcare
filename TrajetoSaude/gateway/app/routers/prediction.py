from fastapi import APIRouter

from app.clients.services import prediction_client

router = APIRouter()


@router.get("/features", summary="Colunas de features do modelo")
async def features():
     return await prediction_client.get("/predict/features")


@router.post("/risk", summary="Predição de risco de evasão")
async def predict_risk(payload: dict):
     return await prediction_client.post("/predict/risk", json=payload)


@router.post("/deslocamento", summary="Calcula UBS no raio de 3km e tempo de deslocamento estimado")
async def calcular_deslocamento(payload: dict):
     return await prediction_client.post("/predict/deslocamento", json=payload)


@router.post("/ingest", summary="Executa pipeline de ingestão e envia artefatos ao GCS")
async def run_ingestion():
     return await prediction_client.post("/ingest/run", timeout=600.0)
