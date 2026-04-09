import time

from fastapi import Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from src.core.session_cookies import SessionCookies
from src.database.db_session import AsyncSessionLocal
from src.database.models.user_model import User

from src.core.logger import log

class SessionTimeoutMiddleware(BaseHTTPMiddleware):
    """Implementa timeout de 10 minutos para nível > 1 por inatividade.

    Também aplica headers de cache-control em todas as respostas e
    renova o cookie ``last_activity`` a cada requisição autenticada.
    """

    TIMEOUT_SECONDS: int = 600  # 10 minutos

    async def dispatch(self, request: Request, call_next) -> Response:
        # 1. Ignora caminhos que não precisam de autenticação/timeout
        if request.url.path.startswith("/static") or request.url.path.startswith(
            "/auth"
        ):
            return await call_next(request)

        user_id = request.cookies.get("user_id")
        session_id = request.cookies.get("session_id")

        if user_id:
            now = time.time()
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(User).filter_by(id=int(user_id))
                )
                user = result.scalar_one_or_none()

                if user:
                    # 2. Verifica se a sessão foi encerrada administrativamente (session_id mudou ou foi limpo)
                    if user.session_id and user.session_id != session_id:
                        response = RedirectResponse(url="/auth/login")
                        SessionCookies.clear_session(response)
                        if request.headers.get("HX-Request"):
                            response.headers["HX-Redirect"] = "/auth/login"
                        log.info(f"Sessão do usuário {user_id} invalidada administrativamente.")
                        return response

                    # 3. Atualiza atividade no banco de dados (para o Admin Panel)
                    user.last_activity = int(now)
                    await session.commit()

                    # 4. Lógica de Timeout por inatividade (nível > 1)
                    if user.user_level > 1:
                        last_activity = request.cookies.get("last_activity")
                        if last_activity:
                            try:
                                last_time = float(last_activity)
                                if (now - last_time) > self.TIMEOUT_SECONDS:
                                    response = RedirectResponse(url="/auth/login")
                                    SessionCookies.clear_session(response)
                                    if request.headers.get("HX-Request"):
                                        response.headers["HX-Redirect"] = "/auth/login"
                                    log.info(f"Sessão do usuário {user_id} expirada por inatividade.")
                                    return response
                            except (ValueError, TypeError):
                                pass

        response = await call_next(request)

        # Headers de segurança / cache
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # Renova o timestamp de última atividade se o usuário estiver logado
        if user_id:
            SessionCookies.set_last_activity(response)

        return response


# Pedi para IA fazer isso aqui. Não faço ideia do que acontece e estou com preguiça de entender.
# Mas funciona.
