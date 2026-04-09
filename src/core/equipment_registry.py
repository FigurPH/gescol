"""EquipmentRegistry — Registro centralizado de modelos de equipamentos.

Para adicionar um novo tipo de equipamento (ex: RF):
  1. Crie o modelo ORM com o campo `serialnumber`.
  2. Adicione a entrada no dict `EQUIPMENT_TABLES` abaixo.

Isso garante que a busca por serialnumber seja feita apenas em tabelas
de equipamentos, e não em outras tabelas do sistema.
"""
from __future__ import annotations

from typing import Optional, Tuple, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.coletor_model import Coletor


class EquipmentRegistry:
    """Registro de todos os modelos de equipamentos atribuíveis.

    Cada entrada mapeia um nome canônico de tipo para o modelo ORM.
    O modelo DEVE ter um campo ``serialnumber`` único.
    """

    EQUIPMENT_TABLES: dict[str, Any] = {
        "coletor": Coletor,
        # "rf": RF,  # Exemplo: adicionar aqui no futuro
    }

    @classmethod
    async def find_by_serialnumber(
        cls, serialnumber: str, db: AsyncSession
    ) -> Tuple[Optional[Any], Optional[str]]:
        """Busca um equipamento pelo número de série em todas as tabelas registradas.

        Returns:
            (equipment_object, equipment_type) se encontrado.
            (None, None) caso contrário.
        """
        sn = serialnumber.strip().upper()

        for equipment_type, model in cls.EQUIPMENT_TABLES.items():
            result = await db.execute(
                select(model).filter(model.serialnumber == sn)
            )
            equipment = result.scalar_one_or_none()
            if equipment:
                return equipment, equipment_type

        return None, None

    @classmethod
    def get_type_for(cls, equipment_object: Any) -> Optional[str]:
        """Retorna o tipo canônico de um objeto de equipamento já carregado."""
        for equipment_type, model in cls.EQUIPMENT_TABLES.items():
            if isinstance(equipment_object, model):
                return equipment_type
        return None
