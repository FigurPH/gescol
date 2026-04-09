from fastapi.responses import RedirectResponse
import uuid
from src.core.session_cookies import SessionCookies
from fastapi import Response
from src.auth.hash_handler import HashHandler
from src.database.models.user_model import User
from sqlalchemy import select
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse

from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db_session import get_db

from src.core.templates import templates
from src.auth.dependencies import get_current_user

from src.core.logger import log
from src.core.rate_limiter import limiter

router = APIRouter(prefix="/auth")


@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("components/login.html", {"request": request})


@router.post("/login", response_class=HTMLResponse)
@limiter.limit("5/minute")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # 1 - Buscar usuário no banco de dados.
    user = await db.execute(select(User).where(User.username == username))
    user = user.scalar_one_or_none()

    if not user or not HashHandler.verify_password(password, user.password):
        log.warning(f"Tentativa de login falhou para o usuário: {username}")

        # Retorna apenas o erro para o target do HTMX (geralmente uma div de erro)
        return HTMLResponse(
            content="<span style='color: #d32f2f; font-weight: bold;'>⚠️ Usuário ou senha inválidos.</span>",
            status_code=200,
        )

    # Criação de resposta vazia que servirá como carrier do Cookie e Redirect
    response = Response()

    session_id = str(uuid.uuid4())
    user.session_id = session_id
    await db.commit()

    SessionCookies.set_session(response, user.id, session_id)

    log.info(f"Usuário {username} logado com sucesso.")

    # Redirecionamento para a página inicial com HTMX
    response.headers["HX-Redirect"] = "/"

    return response


@router.get("/logout", response_class=HTMLResponse)
async def logout():
    response = RedirectResponse(url="/auth/login", status_code=302)
    SessionCookies.clear_session(response)
    response.headers["HX-Refresh"] = "true"
    return response


@router.get("/perfil", response_class=HTMLResponse)
async def perfil(request: Request, user=Depends(get_current_user)):
    return templates.TemplateResponse(
        "components/perfil.html",
        {"request": request, "user": user, "user_name": user.name, "user_level": user.user_level},
    )


@router.post("/perfil/trocar-senha")
async def change_password(
    request: Request,
    senha_atual: str = Form(...),
    nova_senha: str = Form(...),
    confirmar_senha: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    # 1. Validação básica de repetição
    if nova_senha != confirmar_senha:
        return HTMLResponse("<span style='color:red; font-weight:bold;'>❌ As novas senhas não coincidem!</span>")
    
    user_id = request.cookies.get("user_id")
    result = await db.execute(select(User).filter_by(id=int(user_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        return HTMLResponse("Sessão inválida", status_code=401)

    # 2. Verificação da SENHA ATUAL
    if not HashHandler.verify_password(senha_atual, user.password):
        return HTMLResponse("<span style='color:red; font-weight:bold;'>❌ Senha atual incorreta!</span>")

    # 3. Atualização para a NOVA SENHA
    user.password = HashHandler.get_password_hash(nova_senha)
    
    try:
        await db.commit()
        return HTMLResponse("""
            <div style='background: #e8f5e9; padding: 15px; border-radius: 6px; color: #2e7d32; margin-bottom: 15px; text-align: center;'>
                <b>✅ Senha alterada com sucesso!</b>
            </div>
            <script>setTimeout(() => { window.location.reload(); }, 2000);</script>
        """)
    except Exception:
        await db.rollback()
        return HTMLResponse("<span style='color:red'>Erro interno ao salvar.</span>")
