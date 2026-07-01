from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket
from app.schemas import TicketCreate, TicketResponse

router = APIRouter()


@router.post("", response_model=TicketResponse, status_code=201)
def criar_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    valido_ate = datetime.now(timezone.utc) + timedelta(days=1)
    ticket = Ticket(**payload.model_dump(), valido_ate=valido_ate)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}", response_model=TicketResponse)
def buscar_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado.")
    # Atualiza status expirado automaticamente
    if ticket.status == "ativo" and ticket.valido_ate < datetime.now(timezone.utc):
        ticket.status = "expirado"
        db.commit()
        db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/utilizar", response_model=TicketResponse)
def utilizar_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado.")
    if ticket.status != "ativo":
        raise HTTPException(status_code=409, detail=f"Ticket {ticket.status}.")
    if ticket.valido_ate < datetime.now(timezone.utc):
        ticket.status = "expirado"
        db.commit()
        raise HTTPException(status_code=410, detail="Ticket expirado.")
    ticket.status = "utilizado"
    db.commit()
    db.refresh(ticket)
    return ticket
