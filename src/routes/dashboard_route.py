from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select, func
from src.database.db_session import get_db
from src.database.models.coletor_model import Coletor
from src.database.models.atribuicao_model import Atribuicao
from src.auth.dependencies import get_current_user
from src.core.templates import spa_response

from src.core.logger import log


router = APIRouter(prefix="/dashboard")


@router.get("/", response_class=HTMLResponse)
async def get_dashboard(
    request: Request, db=Depends(get_db), user=Depends(get_current_user)
):
    # Query agrupando por CD com estados reais
    # 1. Contar coletores ativos (não em manutenção)
    # 2. Contar coletores inativos (em manutenção)
    # 3. Contar coletores atualmente atribuídos (checkin_time IS NULL na atribuição mais recente)

    # Subquery para pegar atribuições ativas (checkin_time IS NULL)
    active_attributions_sq = (
        select(Atribuicao.coletor_id).filter(Atribuicao.checkin_time == None).subquery()
    )

    query = select(
        Coletor.cd,
        func.count(Coletor.id).filter(Coletor.is_active == 1).label("disponiveis"),
        func.count(Coletor.id).filter(Coletor.is_active == 0).label("inativos"),
        func.count(Coletor.id)
        .filter(Coletor.id.in_(select(active_attributions_sq.c.coletor_id)))
        .label("atribuidos"),
    ).group_by(Coletor.cd)

    if user.user_level < 10:
        query = query.filter(Coletor.cd == user.cd)

    result = await db.execute(query)
    stats_raw = result.all()

    # "disponíveis" reais = ativos - atribuídos (pois atribuídos também são is_active=True)
    stats = []
    for s in stats_raw:
        disp_real = max(0, s.disponiveis - s.atribuidos)
        stats.append(
            {
                "cd": s.cd,
                "disponiveis": disp_real,
                "inativos": s.inativos,
                "atribuidos": s.atribuidos,
            }
        )

    total_disp = sum(s["disponiveis"] for s in stats)
    total_inat = sum(s["inativos"] for s in stats)
    total_atrib = sum(s["atribuidos"] for s in stats)

    context = {
        "request": request,
        "stats": stats,
        "total_disp": total_disp,
        "total_inat": total_inat,
        "total_atrib": total_atrib,
        "is_super": user.user_level == 10,
        "user_name": user.name,
        "user_level": user.user_level,
    }

    log.info(
        f"LOG: {user.username} - Dashboard acessado com sucesso. Total de coletores: {total_disp + total_inat + total_atrib}."
    )

    return spa_response(request, "components/dashboard/dashboard.html", context)
