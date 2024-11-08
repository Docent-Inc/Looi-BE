"""Database changes

Revision ID: bd8e8fa8b4af
Revises: 0b515d647c08
Create Date: 2023-12-26 08:18:25.157583

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'bd8e8fa8b4af'
down_revision = '0b515d647c08'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Calendar', sa.Column('is_generated', sa.Boolean(), nullable=True))
    op.create_index(op.f('ix_Calendar_is_generated'), 'Calendar', ['is_generated'], unique=False)
    op.add_column('Memo', sa.Column('is_generated', sa.Boolean(), nullable=True))
    op.create_index(op.f('ix_Memo_is_generated'), 'Memo', ['is_generated'], unique=False)
    op.add_column('MorningDiary', sa.Column('is_generated', sa.Boolean(), nullable=True))
    op.drop_index('ix_MorningDiary_is_completed', table_name='MorningDiary')
    op.create_index(op.f('ix_MorningDiary_is_generated'), 'MorningDiary', ['is_generated'], unique=False)
    op.drop_column('MorningDiary', 'is_completed')
    op.add_column('NightDiary', sa.Column('is_generated', sa.Boolean(), nullable=True))
    op.create_index(op.f('ix_NightDiary_is_generated'), 'NightDiary', ['is_generated'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_NightDiary_is_generated'), table_name='NightDiary')
    op.drop_column('NightDiary', 'is_generated')
    op.add_column('MorningDiary', sa.Column('is_completed', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.drop_index(op.f('ix_MorningDiary_is_generated'), table_name='MorningDiary')
    op.create_index('ix_MorningDiary_is_completed', 'MorningDiary', ['is_completed'], unique=False)
    op.drop_column('MorningDiary', 'is_generated')
    op.drop_index(op.f('ix_Memo_is_generated'), table_name='Memo')
    op.drop_column('Memo', 'is_generated')
    op.drop_index(op.f('ix_Calendar_is_generated'), table_name='Calendar')
    op.drop_column('Calendar', 'is_generated')
    # ### end Alembic commands ###
