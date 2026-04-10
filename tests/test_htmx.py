import pytest
import logging
from tests.conftest import login_helper

logger = logging.getLogger("src.core.logger")

@pytest.mark.asyncio
async def test_htmx_partial_vs_full_page(client, seed_data):
    logger.info("[TEST] Iniciando teste de fragmentos HTMX")
    from src.main import app
    
    await login_helper(client, "superadmin", "pass123")
    
    # Full Page
    response_full = await client.get("/atribuicoes/")
    assert response_full.status_code == 200
    assert "<!DOCTYPE html>" in response_full.text
    
    # Partial Page
    # Nota: O template usa "Matrícula Colaborador" (sem 'do')
    response_partial = await client.get("/atribuicoes/", headers={"HX-Request": "true"})
    assert response_partial.status_code == 200
    assert "<!DOCTYPE html>" not in response_partial.text
    assert "Matrícula Colaborador" in response_partial.text
    logger.info("[TEST] Fragmentos HTMX validados (String 'Matrícula Colaborador' encontrada)")

@pytest.mark.asyncio
async def test_htmx_oob_toast_fragment(client):
    logger.info("[TEST] Iniciando teste de HTMX OOB Toast")
    from src.core.templates import toast_response
    
    response = toast_response("Msg Teste", is_error=False)
    assert 'hx-swap-oob="beforeend"' in response.body.decode()
    logger.info("[TEST] OOB Toast validado")
