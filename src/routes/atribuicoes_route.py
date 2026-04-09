import datetime

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.core.attribution_views import AttributionViews
from src.core.cd_utils import same_cd
from src.core.equipment_registry import EquipmentRegistry
from src.core.templates import spa_response
from src.database.db_session import get_db
from src.auth.permissions import PermissionManager, Permission
from src.database.models.atribuicao_model import Atribuicao
from src.database.models.colaborador_model import Colaborador
from src.core.logger import log



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
    """
    Busca os dados de um colaborador pelo ID Magalu (matrícula).
    Valida se o colaborador pertence ao mesmo CD do operador (se restrito).
    Verifica se o colaborador já possui um equipamento em uso.
    """
    if not registration.isdigit() or len(registration) != 6:
        return AttributionViews.error_invalid_registration()

    result = await db.execute(
        select(Colaborador).filter(Colaborador.matricula == registration)
    )
    employee = result.scalar_one_or_none()

    if not employee:
        return AttributionViews.error_employee_not_found()

    # Validação de CD
    if user.is_cd_restricted and not same_cd(employee.filial, user.cd):
        log.warning(f"LOG: {user.username} - Acesso negado ao CD {employee.filial} (Usuário do CD {user.cd})")
        return AttributionViews.error_cd_mismatch(employee.filial)

    # Buscar atribuição ativa
    result_attr = await db.execute(
        select(Atribuicao)
        .options(joinedload(Atribuicao.coletor))
        .filter(
            Atribuicao.colaborador_id == employee.id, Atribuicao.checkin_time.is_(None)
        )
    )
    active_attr = result_attr.scalar_one_or_none()

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
    """
    Processa o checkout (atribuição) ou encaminha para return_attribution se houver attribution_id.
    """
    # Fluxo de devolução delegado
    if attribution_id:
        return await return_attribution(
            request=request,
            attribution_id=attribution_id,
            origin=None,
            serialnumber=serialnumber,
            db=db,
            user=user,
        )

    if not employee_id:
        log.error(f"LOG: {user.username} - Erro: Colaborador não informado")
        return AttributionViews.error_no_employee_selected()

    if not serialnumber or not serialnumber.strip():
        log.error(f"LOG: {user.username} - Erro: SN não informado")
        return AttributionViews.error_no_serialnumber()

    # Busca o equipamento pelo número de série em todas as tabelas registradas
    equipment, equipment_type = await EquipmentRegistry.find_by_serialnumber(
        serialnumber, db
    )

    if not equipment:
        log.error(f"LOG: {user.username} - Equipamento SN '{serialnumber}' não encontrado")
        return AttributionViews.error_equipment_not_found(serialnumber)

    if not equipment.is_active:
        log.error(f"LOG: {user.username} - Equipamento {equipment.name} inativo")
        return AttributionViews.error_equipment_inactive(equipment.name)

    # Verifica se o equipamento já está em uso
    result_busy = await db.execute(
        select(Atribuicao).filter(
            Atribuicao.coletor_id == equipment.id, Atribuicao.checkin_time.is_(None)
        )
    )
    if result_busy.scalar_one_or_none():
        log.error(f"LOG: {user.username} - Equipamento {equipment.name} já está em uso")
        return AttributionViews.error_equipment_in_use()

    result_emp = await db.execute(
        select(Colaborador).filter(Colaborador.id == employee_id)
    )
    employee = result_emp.scalar_one_or_none()

    if not employee:
        return AttributionViews.error_employee_lookup_failed()

    result_busy_emp = await db.execute(
        select(Atribuicao).filter(
            Atribuicao.colaborador_id == employee.id, Atribuicao.checkin_time.is_(None)
        )
    )
    if result_busy_emp.scalar_one_or_none():
        log.error(f"LOG: {user.username} - Colaborador {employee.name} já possui equipamento")
        return AttributionViews.error_employee_already_has_collector()

    db.add(
        Atribuicao(
            coletor_id=equipment.id,
            colaborador_id=employee.id,
            user_id=user.id,
            equipment_type=equipment_type,
            checkout_time=datetime.datetime.now(),
        )
    )
    await db.commit()

    log.info(
        f"LOG: {user.username} - Saída: {equipment_type} '{equipment.name}' → {employee.name}"
    )

    return AttributionViews.success_checkout(equipment.name, employee.name)


@router.post("/devolver")
async def return_attribution(
    request: Request,
    attribution_id: int = Form(None),
    origin: str = Form(None),
    serialnumber: str = Form(None),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Processa o checkin (devolução) de um equipamento.
    Exige redigitação do SN para confirmação (exceto via relatórios).
    """
    if not attribution_id:
        return AttributionViews.error_attribution_not_identified()

    result = await db.execute(
        select(Atribuicao)
        .options(joinedload(Atribuicao.coletor), joinedload(Atribuicao.colaborador))
        .filter(Atribuicao.id == attribution_id)
    )
    attribution = result.scalar_one_or_none()

    if not attribution:
        return AttributionViews.error_attribution_not_found()

    # Dupla verificação do equipamento (fora do fluxo de relatórios)
    if origin != "reports":
        if not serialnumber or not serialnumber.strip():
            return AttributionViews.error_no_return_serialnumber()

        informed_sn = serialnumber.strip().upper()
        attributed_sn = (attribution.coletor.serialnumber or "").upper()

        if informed_sn != attributed_sn:
            log.warning(f"LOG: {user.username} - SN incorreto na devolução: {informed_sn} != {attributed_sn}")
            return AttributionViews.error_wrong_equipment(informed_sn=informed_sn)

    attribution.checkin_time = datetime.datetime.now()
    await db.commit()

    equipment_name = attribution.coletor.name
    employee_name = attribution.colaborador.name

    log.info(f"LOG: {user.username} - Devolução: {equipment_name} ← {employee_name} ({origin or 'direta'})")

    if origin == "reports":
        return AttributionViews.success_checkin_from_reports(equipment_name, employee_name)

    return AttributionViews.success_checkin(equipment_name, employee_name)

