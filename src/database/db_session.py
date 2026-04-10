from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
import os
from src.core.logger import log

# --- Imports de todas classes com Modelos para que a Base neutra reconheça os metadados --- #

# noqa: F401 ignora imports não utilizados, sinalizados pelo RUFF (linter)
import src.database.models.user_model  # noqa: F401
import src.database.models.colaborador_model  # noqa: F401
import src.database.models.coletor_model  # noqa: F401
import src.database.models.atribuicao_model  # noqa: F401

DATABASE_URL = os.getenv("DATABASE_URL")

# Engine e Sessionmaker criados globalmente, mas passíveis de reconfiguração
engine = create_async_engine(DATABASE_URL, echo=False, future=True) if DATABASE_URL else None
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
) if engine else None

if engine:
    log.info(f"Conectado ao banco de dados: {engine.url}")
else:
    log.warning("DATABASE_URL não definida. O sistema pode falhar se o banco for acessado sem override.")


async def init_db():
    # Alembic replaces automatic create_all
    # Apenas registra os metadados da conexão com DB
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# Criar nova migration: alembic revision -m "nome_do_que_será_feito". Ex:
# alembic revision -m "cria_tabela_de_coletores"
# Atualizar banco: alembic upgrade head
# Voltar uma migration: alembic downgrade -1
