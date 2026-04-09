"""create_collector_table

Revision ID: 9b2ce875db65
Revises: 279db3fd4c18
Create Date: 2026-04-01 10:10:47.562575

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9b2ce875db65"
down_revision: Union[str, Sequence[str], None] = "279db3fd4c18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "coletores",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String(20), nullable=False),
        sa.Column("model", sa.String(20), nullable=False),
        sa.Column("serialnumber", sa.String(50), nullable=False, unique=True),
        sa.Column("cd", sa.String(5), nullable=False, index=True),
        sa.Column("is_active", sa.SmallInteger, default=1),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("coletores")
