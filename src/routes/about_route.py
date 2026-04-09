from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from src.auth.dependencies import get_current_user
from src.core.templates import spa_response

router = APIRouter(prefix="/sobre")


@router.get("/", response_class=HTMLResponse)
async def about_page(request: Request, user=Depends(get_current_user)):
    """Exibe a página "Sobre" com informações do sistema."""
    context = {
        "request": request,
        "user_name": user.username,
        "user_level": user.user_level,
        # quaisquer outros dados futuros
    }
    return spa_response(request, "components/about/about.html", context)
