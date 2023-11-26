"""Database changes

Revision ID: b3cabd047ac4
Revises: 0a43e5eba695
Create Date: 2023-11-26 21:12:16.763826

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3cabd047ac4'
down_revision = '0a43e5eba695'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('MorningDiary', sa.Column('view_count', sa.Integer(), nullable=True))
    op.add_column('MorningDiary', sa.Column('share_count', sa.Integer(), nullable=True))
    op.add_column('NightDiary', sa.Column('view_count', sa.Integer(), nullable=True))
    op.add_column('NightDiary', sa.Column('share_count', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('NightDiary', 'share_count')
    op.drop_column('NightDiary', 'view_count')
    op.drop_column('MorningDiary', 'share_count')
    op.drop_column('MorningDiary', 'view_count')
    # ### end Alembic commands ###