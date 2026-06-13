"""update_status_and_customer_constraints

Revision ID: 0559ddf19e14
Revises: f7135864cc61
Create Date: 2026-06-13 19:32:45.515547

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0559ddf19e14'
down_revision: Union[str, None] = 'f7135864cc61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop the old order status check constraint FIRST
    op.drop_constraint('ck_orders_status_valid', 'orders', type_='check')
    
    # 2. Update any existing 'pending' orders to 'created'
    op.execute("UPDATE orders SET status = 'created' WHERE status = 'pending'")
    
    # 3. Create the new order status check constraint
    op.create_check_constraint(
        'ck_orders_status_valid',
        'orders',
        "status IN ('created', 'confirmed', 'completed', 'cancelled')"
    )
    
    # 4. Alter server default for orders.status to 'created'
    op.alter_column('orders', 'status', server_default='created')
    
    # 5. Create customer status check constraint
    op.create_check_constraint(
        'ck_customers_status_valid',
        'customers',
        "status IN ('active', 'inactive')"
    )


def downgrade() -> None:
    # 1. Drop customer status check constraint
    op.drop_constraint('ck_customers_status_valid', 'customers', type_='check')
    
    # 2. Alter server default for orders.status back to 'pending'
    op.alter_column('orders', 'status', server_default='pending')
    
    # 3. Drop the new order status check constraint
    op.drop_constraint('ck_orders_status_valid', 'orders', type_='check')
    
    # 4. Update any existing 'created' orders back to 'pending'
    op.execute("UPDATE orders SET status = 'pending' WHERE status = 'created'")
    
    # 5. Create the old order status check constraint
    op.create_check_constraint(
        'ck_orders_status_valid',
        'orders',
        "status IN ('pending', 'confirmed', 'cancelled')"
    )
