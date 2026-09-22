"""add role and refresh_token

Revision ID: 4611485e2e30
Revises: ac1c199ac41d
Create Date: 2026-09-23 00:56:46.288316

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4611485e2e30"
down_revision: Union[str, Sequence[str], None] = "ac1c199ac41d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Определение типа ENUM для PostgreSQL
userrole_enum = postgresql.ENUM("user", "admin", name="userrole")


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Создаем enum тип в PostgreSQL перед добавлением колонки
    userrole_enum.create(op.get_bind(), checkfirst=True)

    # 2. Добавляем колонку role со значением по умолчанию 'user'
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.Enum("user", "admin", name="userrole"),
            server_default="user",
            nullable=False,
        ),
    )

    # 3. Добавляем колонку refresh_token
    op.add_column(
        "users",
        sa.Column("refresh_token", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "refresh_token")
    op.drop_column("users", "role")

    # Удаляем тип enum из базы данных
    userrole_enum.drop(op.get_bind(), checkfirst=True)
