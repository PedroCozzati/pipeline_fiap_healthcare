from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Paciente
from app.schemas import PacienteCreate, PacienteResponse, PacienteUpdate

router = APIRouter()


@router.post("", response_model=PacienteResponse, status_code=201)
def criar_paciente(payload: PacienteCreate, db: Session = Depends(get_db)):
    if db.query(Paciente).filter(Paciente.carteira_sus == payload.carteira_sus).first():
        raise HTTPException(status_code=409, detail="Carteira do SUS já cadastrada.")
    paciente = Paciente(**payload.model_dump())
    db.add(paciente)
    db.commit()
    db.refresh(paciente)
    return paciente


@router.get("/usuario/{usuario_id}", response_model=PacienteResponse)
def buscar_por_usuario(usuario_id: str, db: Session = Depends(get_db)):
    paciente = db.query(Paciente).filter(Paciente.usuario_id == usuario_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return paciente


@router.get("/sus/{carteira_sus}", response_model=PacienteResponse)
def buscar_por_sus(carteira_sus: str, db: Session = Depends(get_db)):
    paciente = db.query(Paciente).filter(Paciente.carteira_sus == carteira_sus).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return paciente


@router.get("/{paciente_id}", response_model=PacienteResponse)
def buscar_paciente(paciente_id: str, db: Session = Depends(get_db)):
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    return paciente


@router.patch("/{paciente_id}", response_model=PacienteResponse)
def atualizar_paciente(paciente_id: str, payload: PacienteUpdate, db: Session = Depends(get_db)):
    paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente não encontrado.")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(paciente, field, value)
    db.commit()
    db.refresh(paciente)
    return paciente
