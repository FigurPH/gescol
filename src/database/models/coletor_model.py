from sqlalchemy import Column, Integer, String, SmallInteger, ForeignKey
from src.database.models.base import Base  # Import de metadados


class Coletor(Base):
    __tablename__ = "coletores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(20), nullable=False)
    model = Column(String(20), nullable=False)
    serialnumber = Column(String(50), nullable=False, unique=True)
    cd = Column(String(5), nullable=False, index=True)
    is_active = Column(SmallInteger, default=1)
    
    

    def __repr__(self) -> str:
        return f"<Coletor(id={self.id})>"