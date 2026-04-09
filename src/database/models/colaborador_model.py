from sqlalchemy import Column, Integer, String, SmallInteger
from src.database.models.base import Base  # Import de metadados


class Colaborador(Base):
    __tablename__ = "colaborador"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    matricula = Column(String(50), unique=True, index=True, nullable=False)
    cargo = Column(String(100), nullable=False)
    turno = Column(Integer, nullable=False)  # 0=ADM, 1=MANHÃ, 2=TARDE, 3=NOITE
    filial = Column(String(50), nullable=False)
    status = Column(SmallInteger, default=1)  # 1=ATIVO, 0=INATIVO

    def __repr__(self) -> str:
        return f"<Colaborador(matricula={self.matricula}, filial={self.filial})>"
