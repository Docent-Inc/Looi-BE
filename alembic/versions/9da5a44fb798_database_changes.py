"""Database changes

Revision ID: 9da5a44fb798
Revises: 7976acae0748
Create Date: 2024-01-11 17:43:44.369207

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9da5a44fb798'
down_revision = '7976acae0748'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('User', sa.Column('device', sa.String(length=10), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('User', 'device')
    # ### end Alembic commands ###
