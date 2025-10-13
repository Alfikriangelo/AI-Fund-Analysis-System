"""add metadata columns for phase 2

Revision ID: f61233fa8911
Revises: 7f7d785a5469
Create Date: 2025-04-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'f61233fa8911'
down_revision = '7f7d785a5469'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Hanya tambahkan kolom baru ke tabel documents
    op.add_column('documents', sa.Column('title', sa.String(500), nullable=True))
    op.add_column('documents', sa.Column('date', sa.String(100), nullable=True))
    op.add_column('documents', sa.Column('document_number', sa.String(200), nullable=True))
    op.add_column('documents', sa.Column('document_type', sa.String(200), nullable=True))

def downgrade() -> None:
    # Hanya hapus kolom jika rollback
    op.drop_column('documents', 'title')
    op.drop_column('documents', 'date')
    op.drop_column('documents', 'document_number')
    op.drop_column('documents', 'document_type')