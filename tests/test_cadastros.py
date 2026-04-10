import pytest
import logging
from tests.conftest import login_helper

logger = logging.getLogger("src.core.logger")

@pytest.mark.asyncio
async def test_access_denied_for_level_1(client, seed_data):
    logger.info("[TEST] Iniciando teste de permissão insuficiente (Level 1)")
    await login_helper(client, "user_b", "pass123")
    
    response = await client.get("/colaboradores/")
    assert response.status_code == 403
    assert "Acesso restrito a administradores" in response.json().get("detail", "")
    logger.info("[TEST] Bloqueio de nível 1 confirmado")

@pytest.mark.asyncio
async def test_admin_cd_isolation_on_listing(client, seed_data):
    logger.info("[TEST] Iniciando teste de isolamento na listagem per CD")
    await login_helper(client, "admin_a", "pass123")
    
    response = await client.get("/colaboradores/")
    assert response.status_code == 200
    assert "Operador CD_A" in response.text
    assert "Operador CD_B" not in response.text
    logger.info("[TEST] Isolamento por CD validado")

@pytest.mark.asyncio
async def test_superadmin_access_all(client, seed_data):
    logger.info("[TEST] Iniciando teste de acesso SuperAdmin global")
    await login_helper(client, "superadmin", "pass123")
    
    response = await client.get("/colaboradores/")
    assert response.status_code == 200
    assert "Operador CD_A" in response.text
    assert "Operador CD_B" in response.text
    logger.info("[TEST] Acesso global do SuperAdmin validado")
