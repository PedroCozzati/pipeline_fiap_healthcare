from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.services import gcs, cloud_sql

router = APIRouter()


class SqlQueryRequest(BaseModel):
     sql: str = Field(..., description="Consulta SQL parametrizada (somente SELECT em produção)")
     params: dict = Field(default_factory=dict)


class GcsUploadRequest(BaseModel):
     blob_name: str
     content: str
     content_type: str = "text/plain"


@router.get("/gcs/list")
def gcs_list(prefix: str = ""):
     try:
          return gcs.list_blobs(prefix)
     except FileNotFoundError as exc:
          raise HTTPException(status_code=404, detail=str(exc)) from exc
     except PermissionError as exc:
          raise HTTPException(status_code=403, detail=str(exc)) from exc
     except ValueError as exc:
          raise HTTPException(status_code=400, detail=str(exc)) from exc
     except Exception as exc:
          raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/gcs/download/{blob_name:path}")
def gcs_download(blob_name: str):
     try:
          return gcs.download_blob_text(blob_name)
     except FileNotFoundError as exc:
          raise HTTPException(status_code=404, detail=str(exc)) from exc
     except FileNotFoundError as exc:
          raise HTTPException(status_code=404, detail=str(exc)) from exc
     except PermissionError as exc:
          raise HTTPException(status_code=403, detail=str(exc)) from exc
     except Exception as exc:
          raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/gcs/upload")
def gcs_upload(payload: GcsUploadRequest):
     try:
          return gcs.upload_blob_text(payload.blob_name, payload.content, payload.content_type)
     except FileNotFoundError as exc:
          raise HTTPException(status_code=404, detail=str(exc)) from exc
     except PermissionError as exc:
          raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/sql/query")
def sql_query(payload: SqlQueryRequest):
     try:
          rows = cloud_sql.execute_query(payload.sql, payload.params)
          return {"rows": rows, "count": len(rows)}
     except RuntimeError as exc:
          raise HTTPException(status_code=503, detail=str(exc)) from exc
     except Exception as exc:
          raise HTTPException(status_code=500, detail=str(exc)) from exc
