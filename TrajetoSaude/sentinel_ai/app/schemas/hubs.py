from pydantic import BaseModel, Field


class HubsRequest(BaseModel):
    bairro: str = Field(..., description="Bairro de residência do paciente")
    rota_trabalho: list[str] = Field(default_factory=list, description="Bairros no trajeto casa→trabalho")


class Hub(BaseModel):
    nome: str
    endereco: str
    distancia_min: int = Field(..., description="Distância estimada em minutos a pé/transporte")
    no_trajeto: bool = Field(..., description="True se está no bairro ou no trajeto do paciente")
    tipo: str = Field(..., description="'hub' ou 'ubs'")


class HubsResponse(BaseModel):
    hubs: list[Hub]
    total: int
