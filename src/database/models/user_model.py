from sqlalchemy import Column, Integer, String, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship
from src.database.models.base import Base  # Import de metadados


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    matricula = Column(
        String(50),
        ForeignKey("colaborador.matricula"),
        unique=True,
        index=True,
        nullable=False,
    )
    username = Column(String(50), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    user_level = Column(SmallInteger, default=1)
    last_activity = Column(Integer, nullable=True)  # Timestamp unix
    session_id = Column(String(255), nullable=True) # UUID ou similar

    # Relacionamento para carregar dados do colaborador associado
    colaborador = relationship(
        "Colaborador",
        foreign_keys=[matricula],
        primaryjoin="User.matricula == Colaborador.matricula",
        lazy="joined",
    )

    def __repr__(self) -> str:
        return f"<User(username={self.username}, level={self.user_level})>"

    @property
    def cd(self) -> str | None:
        """Retorna o CD (filial) do colaborador associado ao usuário."""
        return self.colaborador.filial if self.colaborador else None

    @property
    def name(self) -> str:
        """Retorna o nome real do colaborador ou o username como fallback."""
        return self.colaborador.name if self.colaborador else self.username

    @property
    def is_cd_restricted(self) -> bool:
        """
        Retorna True se o usuário deve ser restrito ao seu próprio CD.
        Apenas SUPERADMIN (nível 10) possui permissão para gerenciar todos os CDs.
        """
        return self.user_level < 10


