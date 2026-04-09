from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

from src.database.db_session import get_db
from src.database.models.coletor_model import Coletor
from src.auth.dependencies import get_current_user
from src.database.models.user_model import User

router = APIRouter(prefix="/api/v1/coletores", tags=["API v1 - Coletores"])

@router.get("/", response_model=List[Dict[str, Any]])
async def list_coletores_json(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Lista de coletores em formato JSON.
    Permite interações Mobile SPA no chão de fábrica do Magalu, 
    acessível de fato por apps Kotlin/Flutter com os WebSessions em cabeçalho.
    """
    query = select(Coletor)
    
    # Filtro dinâmico base nas properties em user_model.py
    if user.is_cd_restricted:
        query = query.filter_by(cd=user.cd)
        
    result = await db.execute(query)
    coletores = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "name": c.name,
            "cd": c.cd,
            "status": c.status,
            "model": c.model,
            "serialnumber": c.serialnumber
        }
        for c in coletores
    ]
