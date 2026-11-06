"""Job identity and category agreements; separate Finance from owner demo role."""
from alembic import op
import sqlalchemy as sa

revision = 'b43e9012aa02'
down_revision = 'a32d8f1b0901'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('karigars', sa.Column('wastage_by_category', sa.JSON(), nullable=False, server_default='{}'))
    op.add_column('gold_transactions', sa.Column('job_number', sa.String(80)))
    op.add_column('gold_transactions', sa.Column('item_category', sa.String(30)))
    op.add_column('gold_transactions', sa.Column('huid', sa.String(6)))
    op.create_index('ix_gold_transactions_job_number', 'gold_transactions', ['job_number'])
    op.execute("UPDATE users SET role='finance_head' WHERE email='finance@karigarflow.com' AND role='admin'")


def downgrade():
    op.drop_index('ix_gold_transactions_job_number', table_name='gold_transactions')
    for column in ['huid', 'item_category', 'job_number']:
        op.drop_column('gold_transactions', column)
    op.drop_column('karigars', 'wastage_by_category')
