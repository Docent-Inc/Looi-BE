"""Database changes

Revision ID: 0b2a93c3ac88
Revises: 24993ec7950a
Create Date: 2023-10-31 14:22:00.340917

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b2a93c3ac88'
down_revision = '24993ec7950a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('User', sa.Column('birth', sa.DateTime(), nullable=True))
    op.add_column('User', sa.Column('push_token', sa.String(length=100), nullable=True))
    op.add_column('User', sa.Column('push_morning', sa.Boolean(), nullable=True))
    op.add_column('User', sa.Column('push_night', sa.Boolean(), nullable=True))
    op.add_column('User', sa.Column('push_report', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('User', 'push_report')
    op.drop_column('User', 'push_night')
    op.drop_column('User', 'push_morning')
    op.drop_column('User', 'push_token')
    op.drop_column('User', 'birth')
    # ### end Alembic commands ###
