from fastapi import APIRouter, Depends, Request, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from src.database.db_session import get_db
from src.database.models.atribuicao_model import Atribuicao
from src.database.models.coletor_model import Coletor
from src.database.models.colaborador_model import Colaborador
from src.auth.dependencies import get_current_user
from src.core.templates import templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
import xlsxwriter
import tempfile
import os
from src.core.logger import log


router = APIRouter(prefix="/relatorios")


async def _apply_report_filters(
    query,
    user,
    collector_name: Optional[str] = None,
    employee_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    cd: Optional[str] = None,
    status: Optional[str] = "ativo",
    equipment_type: Optional[str] = None,
):
    """
    Aplica filtros comuns de relatório a uma query SQLAlchemy.
    Extraído para evitar redundância entre visualização HTML e exportação Excel.
    """
    # Filtro padrão: Apenas em uso (checkin_time nulo)
    if status == "ativo":
        query = query.filter(Atribuicao.checkin_time.is_(None))

    # Identificadores de Join para evitar joins duplicados
    is_collector_joined = False

    # Filtro por CD
    if user.is_cd_restricted:
        # Usuário restrito só vê seu próprio CD
        query = query.join(Atribuicao.coletor).filter(Coletor.cd == user.cd)
        is_collector_joined = True
    elif cd and cd.strip().isdigit():
        # Administradores sem restrição podem filtrar por CD específico
        query = query.join(Atribuicao.coletor).filter(Coletor.cd == int(cd))
        is_collector_joined = True

    # Filtro por Coletor
    if collector_name:
        if not is_collector_joined:
            query = query.join(Atribuicao.coletor)
            is_collector_joined = True
        query = query.filter(Coletor.name.ilike(f"%{collector_name}%"))

    # Filtro por Colaborador
    if employee_name:
        query = query.join(Atribuicao.colaborador).filter(
            Colaborador.name.ilike(f"%{employee_name}%")
        )

    # Filtro por Período
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Atribuicao.checkout_time >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Atribuicao.checkout_time < end_dt)
        except ValueError:
            pass

    # Filtro por Tipo de Equipamento
    if equipment_type:
        query = query.filter(Atribuicao.equipment_type == equipment_type)

    return query.order_by(Atribuicao.checkout_time.asc())


@router.get("/", response_class=HTMLResponse)
async def get_reports_page(
    request: Request,
    collector_name: Optional[str] = Query(None),
    employee_name: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    cd: Optional[str] = Query(None),
    status: Optional[str] = Query("ativo"),
    equipment_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Renderiza a página de relatórios com filtros aplicados."""
    base_query = select(Atribuicao).options(
        joinedload(Atribuicao.coletor), joinedload(Atribuicao.colaborador)
    )

    query = await _apply_report_filters(
        base_query, user, collector_name, employee_name, start_date, end_date, cd, status, equipment_type
    )

    result = await db.execute(query)
    attributions = result.scalars().all()

    context = {
        "request": request,
        "attributions": attributions,
        "user": user,
        "now": datetime.now(),
        "user_name": user.name,
        "user_level": user.user_level,
        "filters": {
            "collector_name": collector_name,
            "employee_name": employee_name,
            "start_date": start_date,
            "end_date": end_date,
            "cd": cd,
            "status": status,
            "equipment_type": equipment_type,
        },
    }

    if request.headers.get("HX-Request"):
        log.info(
            f"LOG: {user.username} - Relatórios filtrados: {len(attributions)} resultados. Filtros: {context['filters']}"
        )
        return templates.TemplateResponse("components/reports.html", context)

    context["partial_template"] = "components/reports.html"
    return templates.TemplateResponse("index.html", context)


@router.get("/exportar-xls")
async def export_reports_xls(
    background_tasks: BackgroundTasks,
    collector_name: Optional[str] = Query(None),
    employee_name: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    cd: Optional[str] = Query(None),
    status: Optional[str] = Query("ativo"),
    equipment_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Exporta o relatório atual para formato Excel (XLSX)."""
    if user.user_level < 9:
        return HTMLResponse("<div class='badge-inactive'>❌ Acesso Negado</div>", status_code=403)

    base_query = select(Atribuicao).options(
        joinedload(Atribuicao.coletor), joinedload(Atribuicao.colaborador)
    )

    query = await _apply_report_filters(
        base_query, user, collector_name, employee_name, start_date, end_date, cd, status, equipment_type
    )

    result = await db.execute(query)
    attributions = result.scalars().all()

    # Em vez de io.BytesIO() em memória RAM, cria um arquivo fisicamente em /tmp
    fd, temp_path = tempfile.mkstemp(suffix=".xlsx")
    os.close(fd) # Fecha o descritor de baixo nível

    workbook = xlsxwriter.Workbook(temp_path)
    worksheet = workbook.add_worksheet("Atribuições")

    # Estilos
    header_style = workbook.add_format({"bold": True, "bg_color": "#0086ff", "font_color": "white", "border": 1})
    date_style = workbook.add_format({"num_format": "dd/mm/yyyy hh:mm", "border": 1})
    border_style = workbook.add_format({"border": 1})

    # Cabeçalho
    headers = [
        "Equipamento", "Modelo", "Série", "Colaborador", "Matrícula",
        "CD", "Saída", "Retorno", "Duração (h)", "Tipo"
    ]
    for col, text in enumerate(headers):
        worksheet.write(0, col, text, header_style)

    # Dados
    for row, attr in enumerate(attributions, 1):
        checkout = attr.checkout_time
        checkin = attr.checkin_time
        duration = round(((checkin or datetime.now()) - checkout).total_seconds() / 3600, 2)

        worksheet.write(row, 0, attr.coletor.name, border_style)
        worksheet.write(row, 1, attr.coletor.model, border_style)
        worksheet.write(row, 2, attr.coletor.serialnumber, border_style)
        worksheet.write(row, 3, attr.colaborador.name, border_style)
        worksheet.write(row, 4, attr.colaborador.matricula, border_style)
        worksheet.write(row, 5, attr.coletor.cd, border_style)
        worksheet.write_datetime(row, 6, checkout.replace(tzinfo=None), date_style)
        
        if checkin:
            worksheet.write_datetime(row, 7, checkin.replace(tzinfo=None), date_style)
        else:
            worksheet.write(row, 7, "EM USO", border_style)
            
        worksheet.write(row, 8, duration, border_style)
        worksheet.write(row, 9, attr.equipment_type or "coletor", border_style)

    worksheet.set_column(0, 9, 18)
    workbook.close()

    log.info(f"LOG: {user.username} - Relatório Excel exportado para Stream Chunking ({len(attributions)} linhas)")

    filename = f"relatorio_atribuicoes_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    
    # Envia o arquivo e define a tarefa de fundo para deletá-lo do disco após conclusão da response
    background_tasks.add_task(os.remove, temp_path)

    return FileResponse(
        path=temp_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename,
    )

