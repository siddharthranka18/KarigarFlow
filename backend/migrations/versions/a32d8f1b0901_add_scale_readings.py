"""Store scale photo evidence and server OCR proposals."""
from alembic import op
import sqlalchemy as sa

revision = 'a32d8f1b0901'
down_revision = '8f1a2b3c4d5e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('scale_readings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('image', sa.LargeBinary, nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('weight', sa.Numeric(10, 3)),
        sa.Column('purity', sa.Numeric(5, 2)),
        sa.Column('confidence', sa.Numeric(5, 4), nullable=False),
        sa.Column('raw_text', sa.Text, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )


def downgrade():
    op.drop_table('scale_readings')
