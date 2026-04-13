import asyncio
import os
import sys
from sqlalchemy import delete

# Ajuste do path para importar src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.db_session import AsyncSessionLocal
from src.database.models.user_model import User
from src.database.models.colaborador_model import Colaborador
from src.database.models.coletor_model import Coletor
from src.auth.hash_handler import HashHandler
from src.core.logger import log

# Configurações do Stress Test
NUM_CDS = 5
TOTAL_PER_CD = 20  # 20 * 5 = 100
STRESS_TAG = "[STRESS-TEST]"

async def seed():
    log.info(f"{STRESS_TAG} Iniciando semeadura de dados para teste de estresse...")
    async with AsyncSessionLocal() as session:
        cds = [f"CD{i:02d}" for i in range(1, NUM_CDS + 1)]
        
        for cd in cds:
            log.info(f"{STRESS_TAG} Populando CD: {cd}")
            for i in range(1, TOTAL_PER_CD + 1):
                unique_suffix = f"{cd}_{i:03d}"
                matricula = f"99{cd[2:]}{i:02d}" # Ex: 990101
                
                # 1. Criar Colaborador
                colaborador = Colaborador(
                    name=f"Stress Colab {unique_suffix}",
                    matricula=matricula,
                    cargo="Operador Stress",
                    turno=1,
                    filial=cd,
                    status=1
                )
                session.add(colaborador)
                
                # 2. Criar Usuário (Nível 1)
                user = User(
                    matricula=matricula,
                    username=f"user_{unique_suffix.lower()}",
                    password=HashHandler.get_password_hash("stress123"),
                    user_level=1
                )
                session.add(user)
                
                # 3. Criar Coletor
                coletor = Coletor(
                    name=f"COL-{unique_suffix}",
                    model="MC33 stress",
                    serialnumber=f"SN-STRESS-{unique_suffix}",
                    cd=cd,
                    is_active=1
                )
                session.add(coletor)
                
        try:
            await session.commit()
            log.info(f"{STRESS_TAG} Semeadura concluída com sucesso!")
        except Exception as e:
            await session.rollback()
            log.error(f"{STRESS_TAG} Erro durante semeadura: {e}")
            raise e

async def teardown():
    log.info(f"{STRESS_TAG} Iniciando limpeza de dados de estresse...")
    async with AsyncSessionLocal() as session:
        try:
            # Remover usuários de estresse
            await session.execute(delete(User).where(User.username.like("user_cd%")))
            # Remover coletores de estresse
            await session.execute(delete(Coletor).where(Coletor.serialnumber.like("SN-STRESS-%")))
            # Remover colaboradores de estresse
            await session.execute(delete(Colaborador).where(Colaborador.matricula.like("99%")))
            
            await session.commit()
            log.info(f"{STRESS_TAG} Limpeza concluída!")
        except Exception as e:
            await session.rollback()
            log.error(f"{STRESS_TAG} Erro durante limpeza: {e}")
            raise e

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "teardown":
        asyncio.run(teardown())
    else:
        asyncio.run(seed())
