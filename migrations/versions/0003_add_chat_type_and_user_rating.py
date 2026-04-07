"""add chat_type and user_rating

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-07 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None

def upgrade():
    # Добавляем колонку chat_type в таблицу queues
    op.add_column('queues', sa.Column('chat_type', sa.String(length=20), nullable=False, server_default='private'))
    # Добавляем колонку user_rating в таблицу watched_history
    op.add_column('watched_history', sa.Column('user_rating', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('queues', 'chat_type')
    op.drop_column('watched_history', 'user_rating')