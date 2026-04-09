from fastapi import Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.db_session import get_db
from src.database.models.user_model import User

from src.auth.permissions import PermissionManager, Permission

from src.core.logger import log


async def get_current_admin(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    """Verifica se o usuário tem permissão de admin e retorna o objeto User."""
    user = await get_current_user(request, db)
    if not PermissionManager.has_permission(user.user_level, Permission.ADMIN_HUB):
        log.warning(
            f"LOG: {user.username} - Tentativa de acesso negada. Nível de acesso insuficiente."
        )
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")

    return user


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User:
    """Verifica apenas se o usuário está logado e retorna o objeto User."""
    user_id = request.cookies.get("user_id")
    if not user_id:
        log.warning(
            f"LOG: {user_id} - Tentativa de acesso negada. Nível de acesso insuficiente."
        )
        raise HTTPException(status_code=401, detail="Não autorizado")

    result = await db.execute(select(User).filter_by(id=int(user_id)))
    user = result.scalar_one_or_none()

    if not user:
        log.warning(
            f"LOG: {user_id} - Tentativa de acesso negada. Usuário não encontrado."
        )
        raise HTTPException(status_code=401, detail="Usuário não encontrado")

    return user

