"""create_atribuicao_table

Revision ID: 77b03eea0f70
Revises: 9b2ce875db65
Create Date: 2026-04-01 10:17:33.211533

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "77b03eea0f70"
down_revision: Union[str, Sequence[str], None] = "9b2ce875db65"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "atribuicao",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("coletor_id", sa.Integer, nullable=False),
        sa.Column("colaborador_id", sa.Integer, nullable=False),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("checkout_time", sa.DateTime, nullable=False),
        sa.Column("checkin_time", sa.DateTime, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["coletor_id"], ["coletores.id"]),
        sa.ForeignKeyConstraint(["colaborador_id"], ["colaborador.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_atribuicao_id"), table_name="atribuicao")
    op.drop_table("atribuicao")
