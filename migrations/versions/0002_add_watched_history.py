"""Add watched history table

Revision ID: 0002
Revises: 0001
Create Date: 2024-04-01 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('watched_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('queue_item_id', sa.Integer(), nullable=False),
        sa.Column('media_id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('accepted_by', sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(['queue_item_id'], ['queue_items.id'], ),
        sa.ForeignKeyConstraint(['media_id'], ['media_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_watched_history_chat_id'), 'watched_history', ['chat_id'], unique=False)
    op.create_index(op.f('ix_watched_history_id'), 'watched_history', ['id'], unique=False)

def downgrade():
    op.drop_table('watched_history')