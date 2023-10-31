"""Database changes

Revision ID: bc24fec43bf6
Revises: b0dada9cfa08
Create Date: 2023-06-27 13:38:50.072199

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'bc24fec43bf6'
down_revision = 'b0dada9cfa08'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass