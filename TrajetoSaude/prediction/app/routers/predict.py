from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.config import resolve_pipeline_base_dir
from app.services.geo_features import contar_ubs_no_raio, estimar_tempo_deslocamento_min
from app.services.model_loader import DEFAULT_FEATURE_COLUMNS, predict_risk, load_model

router = APIRouter()

_UBS_GEOJSON_RELPATH = "raw/gis/geoportal_equipamento_saude_ubs_posto_centro_v2.geojson"


class RiskInput(BaseModel):
     Idade: float = Field(..., ge=0, le=120)
     Tempo_Deslocamento_Min: float = Field(..., ge=0)
     Qtd_UBS_Origem_3km: float = Field(..., ge=0)
     Glicemia_Aferida: float = Field(..., ge=0)


class DeslocamentoInput(BaseModel):
     lat_residencia: float
     lng_residencia: float
     lat_trabalho: Optional[float] = None
     lng_trabalho: Optional[float] = None


@router.get("/features")
def features():
     return {"feature_columns": DEFAULT_FEATURE_COLUMNS}


@router.post("/deslocamento")
def calcular_deslocamento(payload: DeslocamentoInput):
     """Deriva Qtd_UBS_Origem_3km e Tempo_Deslocamento_Min a partir de coordenadas reais do paciente."""
     geojson_path = resolve_pipeline_base_dir() / _UBS_GEOJSON_RELPATH

     qtd_ubs = contar_ubs_no_raio(payload.lat_residencia, payload.lng_residencia, geojson_path)
     tempo_min = estimar_tempo_deslocamento_min(
          payload.lat_residencia, payload.lng_residencia,
          payload.lat_trabalho, payload.lng_trabalho,
     )

     return {
          "qtd_ubs_3km": qtd_ubs,
          "tempo_deslocamento_min": tempo_min,
          "fonte_ubs": "geo_real" if qtd_ubs is not None else "indisponivel",
     }


@router.post("/risk")
def predict(payload: RiskInput, request: Request):
     model = getattr(request.app.state, "model", None)
     if model is None:
          try:
               model = load_model()
               request.app.state.model = model
          except Exception as exc:
               raise HTTPException(status_code=503, detail=f"Modelo ainda não carregado: {exc}")

     return predict_risk(model, payload.model_dump())
