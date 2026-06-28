from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Triagem
from app.schemas import TriagemCreate, TriagemResponse

router = APIRouter()


@router.post("", response_model=TriagemResponse, status_code=201)
def criar_triagem(payload: TriagemCreate, db: Session = Depends(get_db)):
    triagem = Triagem(**payload.model_dump())
    db.add(triagem)
    db.commit()
    db.refresh(triagem)
    return triagem


@router.get("/{triagem_id}", response_model=TriagemResponse)
def buscar_triagem(triagem_id: str, db: Session = Depends(get_db)):
    triagem = db.query(Triagem).filter(Triagem.id == triagem_id).first()
    if not triagem:
        raise HTTPException(status_code=404, detail="Triagem não encontrada.")
    return triagem


@router.get("/paciente/{paciente_id}", response_model=List[TriagemResponse])
def historico_paciente(paciente_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Triagem)
        .filter(Triagem.paciente_id == paciente_id)
        .order_by(Triagem.created_at.desc())
        .all()
    )


@router.get("/agente/{agente_id}", response_model=List[TriagemResponse])
def historico_agente(agente_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Triagem)
        .filter(Triagem.agente_id == agente_id)
        .order_by(Triagem.created_at.desc())
        .all()
    )


@router.patch("/{triagem_id}/predicao", response_model=TriagemResponse)
def atualizar_predicao(
    triagem_id: str,
    risco_probabilidade: float,
    risco_label: int,
    db: Session = Depends(get_db),
):
    triagem = db.query(Triagem).filter(Triagem.id == triagem_id).first()
    if not triagem:
        raise HTTPException(status_code=404, detail="Triagem não encontrada.")
    triagem.risco_probabilidade = risco_probabilidade
    triagem.risco_label = risco_label
    db.commit()
    db.refresh(triagem)
    return triagem
