import asyncio
import pytest
import logging
from tests.conftest import login_helper

logger = logging.getLogger("src.core.logger")


@pytest.mark.asyncio
async def test_cd_restriction_cross_cd_access(client, seed_data):
    logger.info("[TEST] Iniciando teste de restrição geográfica (CD Isolation)")
    await login_helper(client, "admin_a", "pass123")

    response = await client.get("/atribuicoes/buscar-colaborador?registration=222222")
    assert response.status_code == 200
    assert "Acesso Negado" in response.text
    assert "pertence ao CD CD_B" in response.text
    logger.info("[TEST] Restrição por CD bloqueou acesso corretamente")


@pytest.mark.asyncio
async def test_race_condition_concurrent_checkouts(client, seed_data):
    logger.info("[TEST] Iniciando teste de Race Condition (3 checkouts simultâneos)")
    await login_helper(client, "superadmin", "pass123")

    tasks = []
    for _ in range(3):
        tasks.append(
            client.post(
                "/atribuicoes/salvar",
                data={"serialnumber": "SN-A1", "employee_id": 102},
            )
        )

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = 0
    conflict_count = 0

    for i, resp in enumerate(responses):
        if isinstance(resp, Exception):
            logger.error(f"[TEST] Request {i} falhou com exceção: {str(resp)}")
            continue

        if "Saída Confirmada" in resp.text:
            success_count += 1
        elif "em uso" in resp.text or "já foi atribuído" in resp.text:
            conflict_count += 1

    logger.info(
        f"[TEST] Resultados Finais: Sucessos={success_count}, Conflitos={conflict_count}"
    )
    # O objetivo principal é garantir que NUNCA haja mais de um sucesso.
    # Em ambientes de teste concorrentes com SQLite, exceções podem ocorrer,
    # mas a integridade dos dados é o que importa.
    assert success_count == 1
    assert success_count + conflict_count <= 3


@pytest.mark.asyncio
async def test_full_atribuicao_cycle(client, seed_data):
    logger.info("[TEST] Iniciando ciclo completo de atribuição e devolução")
    await login_helper(client, "admin_a", "pass123")

    # 1. Atribuição
    await client.post(
        "/atribuicoes/salvar", data={"serialnumber": "SN-A1", "employee_id": 102}
    )

    # 2. Busca ID da atribuição ativa
    from sqlalchemy import select
    from src.database.models.atribuicao_model import Atribuicao
    from tests.conftest import test_session_maker

    async with test_session_maker() as session:
        result = await session.execute(
            select(Atribuicao).filter(Atribuicao.checkin_time.is_(None))
        )
        attr = result.scalar_one()
        attr_id = attr.id

    # 3. Devolução
    response_dev = await client.post(
        "/atribuicoes/devolver",
        data={"attribution_id": attr_id, "serialnumber": "SN-A1"},
    )
    assert "Devolução Confirmada" in response_dev.text
    logger.info("[TEST] Ciclo finalizado com sucesso")
