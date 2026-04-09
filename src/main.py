from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.core.rate_limiter import limiter

from src.middleware.session_timeout import SessionTimeoutMiddleware
from src.core.templates import templates
from src.database.db_session import init_db, get_db
from src.routes.router import routes
from src.auth.dependencies import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação.
    Inicializa o banco de dados no startup.
    """
    await init_db()
    yield


app = FastAPI(
    title="GesCol - Gestor de Coletores",
    description="Sistema de gestão de coletores e colaboradores",
    version="1.0.0",
    lifespan=lifespan
)

# --- Configurações de Limitação de Requisições ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Configurações de Estáticos ---
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# --- Middlewares ---
app.add_middleware(SessionTimeoutMiddleware)

# --- Registro de Rotas ---
for route in routes:
    app.include_router(route)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Rota principal (SPA Base).
    
    Verifica se o usuário está autenticado. Caso contrário, redireciona para o login.
    Renderiza o template principal (index.html) com os dados do usuário.
    """
    try:
        user = await get_current_user(request, db)
    except HTTPException:
        return RedirectResponse(url="/auth/login", status_code=302)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user_id": user.id,
            "user_level": user.user_level,
            "user_name": user.name or user.username,
        },
    )

