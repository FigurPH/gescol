import asyncio
from src.database.db_session import engine
from src.database.models.base import Base
# ensure models are loaded
import src.database.models.user_model
import src.database.models.colaborador_model

async def drop():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("Dropped all tables successfully.")

asyncio.run(drop())
