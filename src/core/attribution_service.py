import datetime
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.database.models.atribuicao_model import Atribuicao
from src.database.models.colaborador_model import Colaborador
from src.core.equipment_registry import EquipmentRegistry
from src.core.cd_utils import same_cd
from src.core.logger import log

class AttributionService:
    """Serviço central de lógica de negócio para atribuições e devoluções."""

    @staticmethod
    async def get_active_attribution_for_employee(db: AsyncSession, employee_id: int) -> Optional[Atribuicao]:
        """Busca uma atribuição ativa para um colaborador."""
        result = await db.execute(
            select(Atribuicao)
            .options(joinedload(Atribuicao.coletor))
            .filter(Atribuicao.colaborador_id == employee_id, Atribuicao.checkin_time.is_(None))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def validate_and_save_checkout(
        db: AsyncSession,
        user_id: int,
        user_username: str,
        user_cd: str,
        is_cd_restricted: bool,
        employee_id: int,
        serialnumber: str
    ) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """
        Realiza as validações e salva uma nova atribuição.
        
        Returns:
            (success, error_code, equipment_name, employee_name)
        """
        # 1. Buscar Equipamento (Eager load relationships if any, although here it's simple)
        equipment, equipment_type = await EquipmentRegistry.find_by_serialnumber(serialnumber, db)
        if not equipment:
            return False, "equipment_not_found", None, None
        
        if not equipment.is_active:
            return False, "equipment_inactive", equipment.name, None

        # 2. Verificar se equipamento está em uso (Índice único no DB já protege, mas aqui damos erro amigável rápido)
        result_busy = await db.execute(
            select(Atribuicao).filter(Atribuicao.coletor_id == equipment.id, Atribuicao.checkin_time.is_(None))
        )
        if result_busy.scalar_one_or_none():
            return False, "equipment_in_use", equipment.name, None

        # 3. Buscar Colaborador
        result_emp = await db.execute(select(Colaborador).filter(Colaborador.id == employee_id))
        employee = result_emp.scalar_one_or_none()
        if not employee:
            return False, "employee_lookup_failed", None, None

        # 4. Validação de CD
        if is_cd_restricted and not same_cd(employee.filial, user_cd):
            log.warning(f"LOG: {user_username} - Conflito de CD: Colaborador do CD {employee.filial} tentado por Operador do CD {user_cd}")
            return False, "cd_mismatch", None, employee.filial

        # 5. Verificar se colaborador já tem equipamento
        result_busy_emp = await db.execute(
            select(Atribuicao).filter(Atribuicao.colaborador_id == employee.id, Atribuicao.checkin_time.is_(None))
        )
        if result_busy_emp.scalar_one_or_none():
            return False, "employee_already_busy", None, employee.name

        # 6. Salvar
        try:
            new_attr = Atribuicao(
                coletor_id=equipment.id,
                colaborador_id=employee.id,
                user_id=user_id,
                equipment_type=equipment_type,
                checkout_time=datetime.datetime.now(),
            )
            db.add(new_attr)
            await db.commit()
            return True, "success", equipment.name, employee.name
        except IntegrityError:
            await db.rollback()
            return False, "equipment_in_use", equipment.name, None

    @staticmethod
    async def perform_checkin(
        db: AsyncSession,
        attribution_id: int,
        informed_sn: Optional[str] = None,
        bypass_sn_check: bool = False
    ) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """Processa a devolução de um equipamento."""
        result = await db.execute(
            select(Atribuicao)
            .options(joinedload(Atribuicao.coletor), joinedload(Atribuicao.colaborador))
            .filter(Atribuicao.id == attribution_id)
        )
        attribution = result.scalar_one_or_none()
        if not attribution:
            return False, "attribution_not_found", None, None

        if not bypass_sn_check and informed_sn:
            if informed_sn.strip().upper() != (attribution.coletor.serialnumber or "").upper():
                return False, "wrong_equipment", None, None

        attribution.checkin_time = datetime.datetime.now()
        await db.commit()
        return True, "success", attribution.coletor.name, attribution.colaborador.name
