"""Database changes

Revision ID: 02029bab501f
Revises: 467dc45bb6e3
Create Date: 2023-08-16 14:38:40.713571

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '02029bab501f'
down_revision = '467dc45bb6e3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
