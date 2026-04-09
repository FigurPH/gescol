from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.auth.dependencies import get_current_admin
from src.core.templates import spa_response, toast_response
from src.database.models.user_model import User
from src.database.db_session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import time

router = APIRouter(prefix="/cadastros")


@router.get("/", response_class=HTMLResponse)
@router.get("/hub", response_class=HTMLResponse)
async def admin_hub(request: Request, admin: User = Depends(get_current_admin)):
    """Exibe o painel administrativo principal (Hub de Cadastros)."""
    context = {
        "request": request,
        "user_name": admin.name,
        "user_level": admin.user_level,
    }
    return spa_response(request, "components/cadastros/admin_hub.html", context)


@router.get("/sessions", response_class=HTMLResponse)
async def list_sessions(
    request: Request,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista sessões de usuários ativos nos últimos 30 minutos.
    Acesso restrito a SUPERADMIN (nível 10).
    """
    if admin.user_level < 10:
        return HTMLResponse("Acesso negado", status_code=403)

    # Usuários ativos nos últimos 30 minutos (1800 segundos)
    threshold = int(time.time()) - 1800
    result = await db.execute(
        select(User)
        .filter(User.last_activity >= threshold)
        .order_by(User.last_activity.desc())
    )
    active_users = result.scalars().all()

    return spa_response(
        request,
        "components/cadastros/sessions_list.html",
        {"request": request, "users": active_users, "now": int(time.time())},
    )


@router.post("/sessions/terminate/{user_id}")
async def terminate_session(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Finaliza a sessão de um usuário específico, invalidando seu session_id."""
    if admin.user_level < 10:
        return HTMLResponse("Acesso negado", status_code=403)

    result = await db.execute(select(User).filter_by(id=user_id))
    user = result.scalar_one_or_none()

    if user:
        user.session_id = None  # Invalida a sessão no próximo request
        await db.commit()
        # Dispara o Toast via HTMX OOB em vez de texto direto
        return toast_response(f"Sessão de {user.username} encerrada com sucesso.", is_error=False)

    return toast_response("Usuário não encontrado.", is_error=True, status_code=404)

