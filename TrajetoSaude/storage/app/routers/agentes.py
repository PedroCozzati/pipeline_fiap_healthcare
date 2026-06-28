from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AgenteSaude
from app.schemas import AgenteCreate, AgenteResponse

router = APIRouter()


@router.post("", response_model=AgenteResponse, status_code=201)
def criar_agente(payload: AgenteCreate, db: Session = Depends(get_db)):
    agente = AgenteSaude(**payload.model_dump())
    db.add(agente)
    db.commit()
    db.refresh(agente)
    return agente


@router.get("/{agente_id}", response_model=AgenteResponse)
def buscar_agente(agente_id: str, db: Session = Depends(get_db)):
    agente = db.query(AgenteSaude).filter(AgenteSaude.id == agente_id).first()
    if not agente:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")
    return agente


@router.get("/usuario/{usuario_id}", response_model=AgenteResponse)
def buscar_por_usuario(usuario_id: str, db: Session = Depends(get_db)):
    agente = db.query(AgenteSaude).filter(AgenteSaude.usuario_id == usuario_id).first()
    if not agente:
        raise HTTPException(status_code=404, detail="Agente não encontrado.")
    return agente
