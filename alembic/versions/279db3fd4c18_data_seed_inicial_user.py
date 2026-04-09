"""data_seed_inicial_user

Revision ID: 279db3fd4c18
Revises: db7e0cf0c891
Create Date: 2026-03-30 15:03:32.511629

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy.sql import table, column
import sqlalchemy as sa

from src.auth.hash_handler import HashHandler


# revision identifiers, used by Alembic.
revision: str = "279db3fd4c18"
down_revision: Union[str, Sequence[str], None] = "db7e0cf0c891"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

user_pass = HashHandler.get_password_hash("admin")


def upgrade() -> None:
    # --- Insersão de Usuário ADMIN temporário ---
    # Tabela Colaborador
    colaborador_admin = table(
        "colaborador",
        column("id", sa.Integer),
        column("name", sa.String),
        column("matricula", sa.String),
        column("cargo", sa.String),
        column("turno", sa.Integer),
        column("filial", sa.String),
        column("status", sa.SmallInteger),
    )
    op.bulk_insert(
        colaborador_admin,
        [
            {
                "id": 1,
                "name": "Administrador",
                "matricula": "000000",
                "cargo": "Administrador",
                "turno": 0,
                "filial": "SuperADMIN",
                "status": 1,
            }
        ],
    )

    # Tabale User
    user_admin = table(
        "users",
        column("id", sa.Integer),
        column("matricula", sa.String),
        column("username", sa.String),
        column("password", sa.String),
        column("user_level", sa.SmallInteger),
    )
    op.bulk_insert(
        user_admin,
        [
            {
                "id": 1,
                "matricula": "000000",
                "username": "admin",
                "password": user_pass,
                "user_level": 10,
            }
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM users WHERE matricula = '000000'")
    op.execute("DELETE FROM colaborador WHERE matricula = '000000'")
