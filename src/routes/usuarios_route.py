from typing import Optional

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.auth.dependencies import get_current_admin
from src.auth.hash_handler import HashHandler
from src.core.cd_utils import same_cd
from src.database.db_session import get_db
from src.database.models.colaborador_model import Colaborador
from src.database.models.user_model import User
from src.auth.permissions import PermissionManager, Permission
from src.core.templates import templates, toast_response

router = APIRouter(prefix="/cadastros/usuarios")


@router.get("/buscar-colaborador", response_class=HTMLResponse)
async def search_employee_for_user(
    id_magalu: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Busca colaborador para preenchimento automático via HTMX."""
    if not id_magalu or not id_magalu.isdigit():
        return templates.TemplateResponse(
            "components/cadastros/usuario/user_form_fields.html",
            {"request": request, "emp": None, "id_magalu": id_magalu},
        )

    result = await db.execute(select(Colaborador).filter_by(matricula=str(id_magalu)))
    emp = result.scalar_one_or_none()

    if emp and admin.is_cd_restricted and not same_cd(emp.filial, admin.cd):
        return HTMLResponse(
            "<span style='color:red; font-size: 0.8rem;'>⚠️ Este colaborador pertence a outro CD.</span>"
        )

    return templates.TemplateResponse(
        "components/cadastros/usuario/user_form_fields.html",
        {"request": request, "emp": emp, "id_magalu": id_magalu},
    )


@router.get("/", response_class=HTMLResponse)
async def list_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Lista usuários baseada no escopo do admin logado."""
    query = select(User).join(Colaborador, User.matricula == Colaborador.matricula)

    if admin.is_cd_restricted:
        query = query.filter(Colaborador.filial == admin.cd)

    result = await db.execute(query.order_by(User.user_level.desc()))
    users = result.scalars().all()

    return templates.TemplateResponse(
        "components/cadastros/usuario/user_list.html",
        {"request": request, "users": users, "admin_level": admin.user_level},
    )


@router.get("/novo", response_class=HTMLResponse)
async def new_user_form(request: Request, admin: User = Depends(get_current_admin)):
    """Retorna o formulário de criação de usuário."""
    return templates.TemplateResponse(
        "components/cadastros/usuario/user_form.html",
        {"request": request, "admin_level": admin.user_level},
    )


@router.get("/editar/{user_id}", response_class=HTMLResponse)
async def edit_user_form(
    user_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Exibe o formulário de edição para um usuário específico."""
    result = await db.execute(select(User).filter_by(id=user_id))
    user_to_edit = result.scalar_one_or_none()

    if not user_to_edit:
        return HTMLResponse("Usuário não encontrado", status_code=404)

    if admin.is_cd_restricted and user_to_edit.cd != admin.cd:
        return HTMLResponse("Acesso negado", status_code=403)

    return templates.TemplateResponse(
        "components/cadastros/usuario/user_edit_form.html",
        {
            "request": request,
            "user_to_edit": user_to_edit,
            "admin_level": admin.user_level,
        },
    )


@router.post("/update/{user_id}")
async def update_user(
    user_id: int,
    request: Request,
    username: str = Form(...),
    password: Optional[str] = Form(None),
    user_level: int = Form(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Atualiza os dados de um usuário existente."""
    result = await db.execute(select(User).filter_by(id=user_id))
    user = result.scalar_one_or_none()

    if not user:
        return HTMLResponse("Usuário não encontrado", status_code=404)

    if admin.is_cd_restricted and user.cd != admin.cd:
        return HTMLResponse("Não autorizado", status_code=403)

    # Bloqueia promoção para nível >= 9 se o admin não tiver permissão
    if (
        not PermissionManager.has_permission(admin.user_level, Permission.CREATE_ADMINS)
        and user_level >= 9
    ):
        user_level = user.user_level

    user.username = username.strip()
    user.user_level = user_level

    if password and password.strip():
        user.password = HashHandler.get_password_hash(password)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        return HTMLResponse(f"Erro ao atualizar: {str(e)}", status_code=400)

    return await list_users(request, db, admin)


@router.post("/salvar")
async def save_user(
    request: Request,
    id_magalu: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    user_level: int = Form(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Cria um novo usuário vinculado a um ID Magalu."""
    if (
        not PermissionManager.has_permission(admin.user_level, Permission.CREATE_ADMINS)
        and user_level >= 9
    ):
        return HTMLResponse(
            "<div class='welcome-card'><h3 style='color:red'>Erro: Nível de acesso insuficiente.</h3>"
            "<button hx-get='/cadastros/usuarios/novo' hx-target='#content' class='magalu-btn'>Voltar</button></div>"
        )

    new_user = User(
        matricula=id_magalu.strip(),
        username=username.strip(),
        password=HashHandler.get_password_hash(password),
        user_level=user_level,
    )

    try:
        db.add(new_user)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return HTMLResponse(
            "<div class='welcome-card'><h3 style='color:red'>Erro: Username ou Matrícula já em uso.</h3>"
            "<button hx-get='/cadastros/usuarios/novo' hx-target='#content' class='magalu-btn'>Voltar</button></div>"
        )

    return await list_users(request, db, admin)


@router.delete("/excluir/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """Exclui um usuário do sistema com validações de hierarquia e CD."""
    result = await db.execute(select(User).filter_by(id=user_id))
    user_to_delete = result.scalar_one_or_none()

    if not user_to_delete:
        return HTMLResponse("Usuário não encontrado", status_code=404)

    if user_to_delete.id == admin.id:
        return toast_response("Erro: Você não pode excluir sua própria conta!", status_code=403)

    if admin.is_cd_restricted:
        if user_to_delete.cd != admin.cd:
            return toast_response("Erro: Não autorizado (CD diferente).", status_code=403)

        if (
            not PermissionManager.has_permission(admin.user_level, Permission.CREATE_ADMINS)
            and user_to_delete.user_level >= 9
        ):
            return toast_response("Erro: Você não pode excluir administradores.", status_code=403)

    await db.delete(user_to_delete)
    await db.commit()

    return HTMLResponse(status_code=200)

