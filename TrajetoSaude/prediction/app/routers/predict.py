from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.model_loader import DEFAULT_FEATURE_COLUMNS, predict_risk

router = APIRouter()


class RiskInput(BaseModel):
     Idade: float = Field(..., ge=0, le=120)
     Tempo_Deslocamento_Min: float = Field(..., ge=0)
     Qtd_UBS_Origem_3km: float = Field(..., ge=0)
     Glicemia_Aferida: float = Field(..., ge=0)


@router.get("/features")
def features():
     return {"feature_columns": DEFAULT_FEATURE_COLUMNS}


@router.post("/risk")
def predict(payload: RiskInput, request: Request):
     model = getattr(request.app.state, "model", None)
     if model is None:
          raise HTTPException(status_code=503, detail="Modelo ainda não carregado.")
     return predict_risk(model, payload.model_dump())
