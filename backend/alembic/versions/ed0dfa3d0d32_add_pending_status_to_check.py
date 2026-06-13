"""add_pending_status_to_check

Revision ID: ed0dfa3d0d32
Revises: 0559ddf19e14
Create Date: 2026-06-13 19:59:34.435976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed0dfa3d0d32'
down_revision: Union[str, None] = '0559ddf19e14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop old constraint
    op.drop_constraint('ck_orders_status_valid', 'orders', type_='check')
    
    # 2. Create updated constraint
    op.create_check_constraint(
        'ck_orders_status_valid',
        'orders',
        "status IN ('created', 'pending', 'confirmed', 'completed', 'cancelled')"
    )


def downgrade() -> None:
    # 1. Drop updated constraint
    op.drop_constraint('ck_orders_status_valid', 'orders', type_='check')
    
    # 2. Recreate old constraint
    op.create_check_constraint(
        'ck_orders_status_valid',
        'orders',
        "status IN ('created', 'confirmed', 'completed', 'cancelled')"
    )
