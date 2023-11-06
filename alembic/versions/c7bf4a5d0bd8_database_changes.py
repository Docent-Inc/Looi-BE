"""Database changes

Revision ID: c7bf4a5d0bd8
Revises: e5384de947ec
Create Date: 2023-11-05 22:47:08.093041

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7bf4a5d0bd8'
down_revision = 'e5384de947ec'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Dashboard', sa.Column('today_user', sa.Integer(), nullable=False))
    op.add_column('Dashboard', sa.Column('today_chat', sa.Integer(), nullable=False))
    op.add_column('Dashboard', sa.Column('today_cost', sa.FLOAT(), nullable=False))
    op.add_column('Dashboard', sa.Column('today_morning_diary', sa.Integer(), nullable=False))
    op.add_column('Dashboard', sa.Column('today_night_diary', sa.Integer(), nullable=False))
    op.add_column('Dashboard', sa.Column('today_calender', sa.Integer(), nullable=False))
    op.add_column('Dashboard', sa.Column('today_memo', sa.Integer(), nullable=False))
    op.add_column('Dashboard', sa.Column('create_date', sa.DateTime(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Dashboard', 'create_date')
    op.drop_column('Dashboard', 'today_memo')
    op.drop_column('Dashboard', 'today_calender')
    op.drop_column('Dashboard', 'today_night_diary')
    op.drop_column('Dashboard', 'today_morning_diary')
    op.drop_column('Dashboard', 'today_cost')
    op.drop_column('Dashboard', 'today_chat')
    op.drop_column('Dashboard', 'today_user')
    # ### end Alembic commands ###