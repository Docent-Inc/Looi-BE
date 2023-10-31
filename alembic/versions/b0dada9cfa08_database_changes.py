"""Database changes

Revision ID: b0dada9cfa08
Revises: 4d90638fb0fe
Create Date: 2023-06-27 09:15:13.685576

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'b0dada9cfa08'
down_revision = '4d90638fb0fe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass