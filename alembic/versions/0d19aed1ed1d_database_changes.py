"""Database changes

Revision ID: 0d19aed1ed1d
Revises: 9da5a44fb798
Create Date: 2024-01-17 18:46:23.522023

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d19aed1ed1d'
down_revision = '9da5a44fb798'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('MorningDiary', sa.Column('is_like', sa.Boolean(), nullable=True))
    op.add_column('NightDiary', sa.Column('is_like', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('NightDiary', 'is_like')
    op.drop_column('MorningDiary', 'is_like')
    # ### end Alembic commands ###