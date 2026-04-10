import pytest
import logging
from tests.conftest import login_helper

logger = logging.getLogger("src.core.logger")

@pytest.mark.asyncio
async def test_login_flow_success(client, seed_data):
    logger.info("[TEST] Iniciando teste de login com sucesso")
    response = await client.post(
        "/auth/login",
        data={"username": "superadmin", "password": "pass123"}
    )
    assert response.status_code == 200
    assert response.headers.get("HX-Redirect") == "/"
    assert "user_id" in client.cookies
    logger.info("[TEST] Login realizado com sucesso")

@pytest.mark.asyncio
async def test_login_flow_failure(client, seed_data):
    logger.info("[TEST] Iniciando teste de login com senha incorreta")
    response = await client.post(
        "/auth/login",
        data={"username": "superadmin", "password": "wrongpassword"}
    )
    assert response.status_code == 200
    assert "Usuário ou senha inválidos" in response.text
    logger.info("[TEST] Falha de login detectada")

@pytest.mark.asyncio
async def test_security_rate_limiting(client, seed_data):
    logger.info("[TEST] Iniciando teste de Rate Limiting (SlowAPI)")
    from src.main import app
    app.state.limiter.enabled = True
    try:
        # 5 attempts are allowed
        for _ in range(5):
            await client.post("/auth/login", data={"username": "fake", "password": "f"})
        
        response = await client.post("/auth/login", data={"username": "fake", "password": "f"})
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.text
    finally:
        app.state.limiter.enabled = False
    logger.info("[TEST] 429 bloqueou excesso de tentativas")

@pytest.mark.asyncio
async def test_logout(client, seed_data):
    logger.info("[TEST] Iniciando teste de logout")
    await login_helper(client, "superadmin", "pass123")
    response = await client.get("/auth/logout")
    assert response.status_code == 302
    assert response.headers.get("HX-Refresh") == "true"
    logger.info("[TEST] Logout OK")
