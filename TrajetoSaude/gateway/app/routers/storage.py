from fastapi import APIRouter

from app.clients.services import storage_client

router = APIRouter()


@router.get("/blobs", summary="Lista objetos no bucket GCS")
async def list_blobs(prefix: str = ""):
     return await storage_client.get("/storage/gcs/list", params={"prefix": prefix})


@router.get("/blobs/{blob_name:path}", summary="Baixa conteúdo de um objeto GCS")
async def download_blob(blob_name: str):
     return await storage_client.get(f"/storage/gcs/download/{blob_name}")


@router.post("/query", summary="Executa consulta SQL no Cloud SQL")
async def run_query(payload: dict):
     return await storage_client.post("/storage/sql/query", json=payload)
