"""initial_schema

Revision ID: 5cbd9b99e7d4
Revises: 
Create Date: 2026-11-04 14:24:13.584388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5cbd9b99e7d4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. karigars
    op.create_table(
        'karigars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('karigar_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('specialization', sa.String(length=100), nullable=True),
        sa.Column('benchmark_wastage_percent', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('opening_balance_gross', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('opening_balance_fine', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_karigars_id'), 'karigars', ['id'], unique=False)
    op.create_index(op.f('ix_karigars_karigar_code'), 'karigars', ['karigar_code'], unique=True)

    # 3. gold_transactions
    op.create_table(
        'gold_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slip_number', sa.String(length=100), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('karigar_id', sa.Integer(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('item_description', sa.String(length=255), nullable=False),
        sa.Column('gross_weight', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('stone_weight', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('net_weight', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('purity_percent', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('fine_weight', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('allowed_wastage_percent', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('actual_wastage_weight', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('wastage_variance_weight', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('is_loss_alert', sa.Boolean(), nullable=False),
        sa.Column('scale_reading_confirmed', sa.Boolean(), nullable=False),
        sa.Column('scale_image_url', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['karigar_id'], ['karigars.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gold_transactions_id'), 'gold_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_gold_transactions_slip_number'), 'gold_transactions', ['slip_number'], unique=True)
    op.create_index(op.f('ix_gold_transactions_karigar_id'), 'gold_transactions', ['karigar_id'], unique=False)
    op.create_index(op.f('ix_gold_transactions_created_at'), 'gold_transactions', ['created_at'], unique=False)

    # 4. gold_inventory
    op.create_table(
        'gold_inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lot_code', sa.String(length=50), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('gross_weight', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('purity_percent', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('fine_weight', sa.Numeric(precision=10, scale=3), nullable=False),
        sa.Column('location', sa.String(length=100), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gold_inventory_id'), 'gold_inventory', ['id'], unique=False)
    op.create_index(op.f('ix_gold_inventory_lot_code'), 'gold_inventory', ['lot_code'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_gold_inventory_lot_code'), table_name='gold_inventory')
    op.drop_index(op.f('ix_gold_inventory_id'), table_name='gold_inventory')
    op.drop_table('gold_inventory')

    op.drop_index(op.f('ix_gold_transactions_created_at'), table_name='gold_transactions')
    op.drop_index(op.f('ix_gold_transactions_karigar_id'), table_name='gold_transactions')
    op.drop_index(op.f('ix_gold_transactions_slip_number'), table_name='gold_transactions')
    op.drop_index(op.f('ix_gold_transactions_id'), table_name='gold_transactions')
    op.drop_table('gold_transactions')

    op.drop_index(op.f('ix_karigars_karigar_code'), table_name='karigars')
    op.drop_index(op.f('ix_karigars_id'), table_name='karigars')
    op.drop_table('karigars')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
