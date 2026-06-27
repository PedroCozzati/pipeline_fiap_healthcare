from pydantic import BaseModel, Field


class RiskRequest(BaseModel):
    idade: float = Field(..., ge=0, le=120, description="Idade do paciente em anos")
    tempo_deslocamento_min: float = Field(..., ge=0, description="Tempo de deslocamento diário em minutos")
    qtd_ubs_origem_3km: float = Field(..., ge=0, description="Quantidade de UBS num raio de 3km da residência")
    glicemia_aferida: float = Field(..., ge=0, description="Glicemia aferida em mg/dL")


class RiskResponse(BaseModel):
    risk_probability: float = Field(..., description="Probabilidade de evasão ao tratamento (0–1)")
    risk_label: int = Field(..., description="0 = baixo risco, 1 = alto risco")
    risk_label_texto: str
    features_usadas: dict[str, float]
