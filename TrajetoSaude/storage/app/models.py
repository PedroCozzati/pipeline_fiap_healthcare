import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Paciente(Base):
    __tablename__ = "pacientes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(String, nullable=False, index=True)  # ref auth service
    nome = Column(String, nullable=False)
    carteira_sus = Column(String, unique=True, nullable=False, index=True)
    data_nascimento = Column(String, nullable=True)  # ISO date string

    # Localização
    endereco = Column(String, nullable=True)
    cidade = Column(String, nullable=True)
    estado = Column(String, nullable=True)
    cep = Column(String, nullable=True)
    lat_residencia = Column(Float, nullable=True)
    lng_residencia = Column(Float, nullable=True)

    # Local de trabalho
    local_trabalho = Column(String, nullable=True)
    lat_trabalho = Column(Float, nullable=True)
    lng_trabalho = Column(Float, nullable=True)
    rota_trabalho = Column(String, nullable=True)  # JSON serializado

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    triagens = relationship("Triagem", back_populates="paciente")
    tickets = relationship("Ticket", back_populates="paciente")


class AgenteSaude(Base):
    __tablename__ = "agentes_saude"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(String, nullable=False, index=True)  # ref auth service
    nome = Column(String, nullable=False)
    registro_profissional = Column(String, nullable=True)
    especialidade = Column(String, nullable=True)
    ubs_vinculada = Column(String, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    triagens = relationship("Triagem", back_populates="agente")


class Triagem(Base):
    __tablename__ = "triagens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    agente_id = Column(UUID(as_uuid=True), ForeignKey("agentes_saude.id"), nullable=True)

    glicemia = Column(Float, nullable=True)
    pressao_sistolica = Column(Integer, nullable=True)
    pressao_diastolica = Column(Integer, nullable=True)

    # Resultado da predição
    risco_probabilidade = Column(Float, nullable=True)
    risco_label = Column(Integer, nullable=True)  # 0 = baixo, 1 = alto

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    paciente = relationship("Paciente", back_populates="triagens")
    agente = relationship("AgenteSaude", back_populates="triagens")
    ticket = relationship("Ticket", back_populates="triagem", uselist=False)


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paciente_id = Column(UUID(as_uuid=True), ForeignKey("pacientes.id"), nullable=False)
    triagem_id = Column(UUID(as_uuid=True), ForeignKey("triagens.id"), nullable=False)

    ubs_encaminhamento = Column(String, nullable=False)
    status = Column(String, default="ativo")  # ativo | utilizado | expirado
    valido_ate = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    paciente = relationship("Paciente", back_populates="tickets")
    triagem = relationship("Triagem", back_populates="ticket")
