"""add_idempotency_key_and_related_slip

Revision ID: 8f1a2b3c4d5e
Revises: 5cbd9b99e7d4
Create Date: 2026-11-04 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f1a2b3c4d5e'
down_revision: Union[str, Sequence[str], None] = '5cbd9b99e7d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('gold_transactions', sa.Column('idempotency_key', sa.String(length=100), nullable=True))
    op.add_column('gold_transactions', sa.Column('related_slip_number', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_gold_transactions_idempotency_key'), 'gold_transactions', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_gold_transactions_related_slip_number'), 'gold_transactions', ['related_slip_number'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_gold_transactions_related_slip_number'), table_name='gold_transactions')
    op.drop_index(op.f('ix_gold_transactions_idempotency_key'), table_name='gold_transactions')
    op.drop_column('gold_transactions', 'related_slip_number')
    op.drop_column('gold_transactions', 'idempotency_key')

