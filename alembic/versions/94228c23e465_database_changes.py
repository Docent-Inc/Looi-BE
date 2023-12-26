"""Database changes

Revision ID: 94228c23e465
Revises: bd8e8fa8b4af
Create Date: 2023-12-26 10:44:41.590459

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '94228c23e465'
down_revision = 'bd8e8fa8b4af'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('NightDiary', sa.Column('resolution', sa.String(length=1000), nullable=True))
    op.add_column('NightDiary', sa.Column('main_keyword', sa.String(length=200), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('NightDiary', 'main_keyword')
    op.drop_column('NightDiary', 'resolution')
    # ### end Alembic commands ###
