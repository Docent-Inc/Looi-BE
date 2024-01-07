"""Database changes

Revision ID: 83f196e88bad
Revises: 272b90580245
Create Date: 2024-01-07 11:03:34.587106

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83f196e88bad'
down_revision = '272b90580245'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('User', sa.Column('push_schedule', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('User', 'push_schedule')
    # ### end Alembic commands ###
