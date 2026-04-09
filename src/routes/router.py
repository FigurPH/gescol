"""
Agregador de rotas da aplicação.
Importa todos os roteadores individuais e os expõe em uma lista única para registro no main.py.
"""
from .auth_router import router as auth_router

from .about_route import router as about_router
from .admin_panel_route import router as admin_router
from .coletores_admin_route import router as coletores_admin_router
from .colaboradores_route import router as colaboradores_router
from .usuarios_route import router as usuarios_router
from .atribuicoes_route import router as atribuicoes_router
from .relatorios_route import router as relatorios_router
from .dashboard_route import router as dashboard_router
from src.api.v1.coletores_api import router as api_v1_coletores_router

routes = [
    auth_router,
    about_router,
    admin_router,
    coletores_admin_router,
    colaboradores_router,
    usuarios_router,
    atribuicoes_router,
    relatorios_router,
    dashboard_router,
    api_v1_coletores_router,
]
