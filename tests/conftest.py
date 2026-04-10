import os
import asyncio
import logging
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import event

# 1. Configuração de Ambiente e Logs
TEST_DB_FILE = "tests/test_final_concurrent.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

test_logger = logging.getLogger("src.core.logger")
test_logger.setLevel(logging.INFO)
for h in test_logger.handlers[:]: test_logger.removeHandler(h)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(levelname)s: [TEST] %(message)s'))
test_logger.addHandler(console_handler)

from src.main import app
from src.database import db_session as db_module
from src.database.models.base import Base
from src.database.models.user_model import User
from src.database.models.colaborador_model import Colaborador
from src.database.models.coletor_model import Coletor
from src.auth.hash_handler import HashHandler

# 2. Motor de Banco Robusto para Concorrência
# Usamos um arquivo real com WAL mode para permitir múltiplas conexões simultâneas
engine_test = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
)

@event.listens_for(engine_test.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

test_session_maker = async_sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)

# Monkeypatch
db_module.engine = engine_test
db_module.AsyncSessionLocal = test_session_maker

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db_schema():
    # Remover arquivo antigo se existir
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
        
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # No final removemos
    # if os.path.exists(TEST_DB_FILE): os.remove(TEST_DB_FILE)

@pytest_asyncio.fixture(autouse=True)
async def clean_database():
    yield
    async with engine_test.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

@pytest_asyncio.fixture
async def db_session():
    async with test_session_maker() as session:
        yield session

@pytest.fixture(autouse=True)
def override_get_db():
    async def _get_db_override():
        async with test_session_maker() as session:
            yield session
    app.dependency_overrides[db_module.get_db] = _get_db_override

@pytest_asyncio.fixture
async def client():
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def seed_data(db_session):
    c1 = Colaborador(id=101, name="Admin Colab", matricula="999999", cargo="TI", turno=0, filial="CD_WEB", status=1)
    c2 = Colaborador(id=102, name="Operador CD_A", matricula="111111", cargo="Op", turno=1, filial="CD_A", status=1)
    c3 = Colaborador(id=103, name="Operador CD_B", matricula="222222", cargo="Op", turno=1, filial="CD_B", status=1)
    db_session.add_all([c1, c2, c3])
    
    u1 = User(id=201, matricula="999999", username="superadmin", password=HashHandler.get_password_hash("pass123"), user_level=10)
    u2 = User(id=202, matricula="111111", username="admin_a", password=HashHandler.get_password_hash("pass123"), user_level=9)
    u3 = User(id=203, matricula="222222", username="user_b", password=HashHandler.get_password_hash("pass123"), user_level=1)
    db_session.add_all([u1, u2, u3])
    
    col_a = Coletor(id=301, name="COL-A1", model="Z", serialnumber="SN-A1", cd="CD_A", is_active=1)
    col_b = Coletor(id=302, name="COL-B1", model="Z", serialnumber="SN-B1", cd="CD_B", is_active=1)
    db_session.add_all([col_a, col_b])
    
    await db_session.commit()
    return {"u1": u1, "u2": u2, "u3": u3}

async def login_helper(client, username, password):
    if hasattr(app.state, "limiter"):
        app.state.limiter.enabled = False
    resp = await client.post("/auth/login", data={"username": username, "password": password})
    assert resp.status_code == 200
    assert "user_id" in client.cookies
    assert client.cookies.get("user_id") != ""
