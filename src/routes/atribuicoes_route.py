from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.attribution_views import AttributionViews
from src.core.cd_utils import same_cd
from src.core.templates import spa_response
from src.database.db_session import get_db
from src.auth.permissions import PermissionManager, Permission
from src.database.models.colaborador_model import Colaborador
from src.core.logger import log



from src.core.attribution_service import AttributionService

router = APIRouter(prefix="/atribuicoes")


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------


@router.get("/", response_class=HTMLResponse)
async def get_attribution_page(request: Request, user=Depends(get_current_user)):
    """Exibe a página principal de atribuição de coletores."""
    context = {
        "request": request,
        "user_id": user.id,
        "user_name": user.name,
        "user_level": user.user_level,
    }
    return spa_response(request, "components/atribuicoes/attribution.html", context)


@router.get("/buscar-colaborador", response_class=HTMLResponse)
async def lookup_employee(
    registration: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Busca dados de um colaborador e verifica se possui equipamentos em uso."""
    if not registration.isdigit() or len(registration) != 6:
        return AttributionViews.error_invalid_registration()

    result = await db.execute(select(Colaborador).filter(Colaborador.matricula == registration))
    employee = result.scalar_one_or_none()

    if not employee:
        return AttributionViews.error_employee_not_found()

    # Validação de CD
    if user.is_cd_restricted and not same_cd(employee.filial, user.cd):
        log.warning(f"LOG: {user.username} - Bloqueio CD: {employee.filial} (Usuário: {user.cd})")
        return AttributionViews.error_cd_mismatch(employee.filial)

    # Buscar atribuição ativa via Serviço
    active_attr = await AttributionService.get_active_attribution_for_employee(db, employee.id)

    if active_attr:
        return AttributionViews.info_employee_with_collector(
            employee_id=employee.id,
            employee_name=employee.name,
            attribution_id=active_attr.id,
            checkout_time=active_attr.checkout_time.strftime("%H:%M"),
            collector_name=active_attr.coletor.name,
            equipment_type=active_attr.equipment_type,
            show_collector_name=PermissionManager.has_permission(
                user.user_level, Permission.SHOW_COLLECTOR_NAME
            ),
        )

    return AttributionViews.info_employee_ready(
        employee_id=employee.id,
        employee_name=employee.name,
        employee_role=employee.cargo,
        employee_cd=employee.filial,
    )


@router.post("/salvar")
async def save_attribution(
    request: Request,
    serialnumber: str = Form(None),
    employee_id: int = Form(None),
    attribution_id: int = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Processa o checkout (atribuição) via serviço."""
    if attribution_id:
        return await return_attribution(request, attribution_id, None, serialnumber, db, user)

    if not employee_id:
        return AttributionViews.error_no_employee_selected()

    if not serialnumber or not serialnumber.strip():
        return AttributionViews.error_no_serialnumber()

    # Executa lógica de checkout via Serviço
    success, error_code, eq_name, emp_name = await AttributionService.validate_and_save_checkout(
        db=db,
        user_id=user.id,
        user_username=user.username,
        user_cd=user.cd or "N/A",
        is_cd_restricted=user.is_cd_restricted,
        employee_id=employee_id,
        serialnumber=serialnumber
    )

    if not success:
        if error_code == "equipment_not_found":
            return AttributionViews.error_equipment_not_found(serialnumber)
        if error_code == "equipment_inactive":
            return AttributionViews.error_equipment_inactive(eq_name)
        if error_code == "equipment_in_use":
            return AttributionViews.error_equipment_in_use()
        if error_code == "employee_lookup_failed":
            return AttributionViews.error_employee_lookup_failed()
        if error_code == "cd_mismatch":
            return AttributionViews.error_cd_mismatch(emp_name)
        if error_code == "employee_already_busy":
            return AttributionViews.error_employee_already_has_collector()
        return AttributionViews.error_attribution_not_identified()

    log.info(f"LOG: {user.username} - checkout: {eq_name} -> {emp_name}")
    return AttributionViews.success_checkout(eq_name, emp_name)


@router.post("/devolver")
async def return_attribution(
    request: Request,
    attribution_id: int = Form(None),
    origin: str = Form(None),
    serialnumber: str = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Processa o checkin (devolução) via serviço."""
    if not attribution_id:
        return AttributionViews.error_attribution_not_identified()

    success, error_code, eq_name, emp_name = await AttributionService.perform_checkin(
        db=db,
        attribution_id=attribution_id,
        informed_sn=serialnumber,
        bypass_sn_check=(origin == "reports")
    )

    if not success:
        if error_code == "attribution_not_found":
            return AttributionViews.error_attribution_not_found()
        if error_code == "wrong_equipment":
            return AttributionViews.error_wrong_equipment(informed_sn=serialnumber)
        return AttributionViews.error_attribution_not_identified()

    log.info(f"LOG: {user.username} - devolução: {eq_name} <- {emp_name}")
    
    if origin == "reports":
        return AttributionViews.success_checkin_from_reports(eq_name, emp_name)
    return AttributionViews.success_checkin(eq_name, emp_name)

