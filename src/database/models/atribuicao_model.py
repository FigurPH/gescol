from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from src.database.models.base import Base  # Import de metadados
from datetime import datetime


class Atribuicao(Base):
    __tablename__ = "atribuicao"

    id = Column(Integer, primary_key=True, index=True)
    coletor_id = Column(Integer, nullable=False)
    colaborador_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    equipment_type = Column(String(20), nullable=False, default="coletor")

    checkout_time = Column(DateTime, nullable=False, default=datetime.now())
    checkin_time = Column(DateTime, nullable=True)

    coletor = relationship(
        "Coletor",
        primaryjoin="Atribuicao.coletor_id == Coletor.id",
        foreign_keys=[coletor_id]
    )
    colaborador = relationship(
        "Colaborador",
        primaryjoin="Atribuicao.colaborador_id == Colaborador.id",
        foreign_keys=[colaborador_id]
    )

    def __repr__(self) -> str:
        return f"<Atribuicao(id={self.id})>"
