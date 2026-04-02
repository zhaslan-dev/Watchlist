"""Initial migration with BigInteger and ENUM

Revision ID: 0001
Revises:
Create Date: 2024-04-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mediasource') THEN
                CREATE TYPE mediasource AS ENUM ('kinopoisk', 'manual');
            END IF;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'queueitemstatus') THEN
                CREATE TYPE queueitemstatus AS ENUM ('pending', 'accepted', 'rejected');
            END IF;
        END $$;
    """)

    op.create_table('media_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.String(length=2000), nullable=True),
        sa.Column('poster_url', sa.String(length=500), nullable=True),
        sa.Column('rating', sa.Float(), nullable=True),
        sa.Column('source', postgresql.ENUM('kinopoisk', 'manual', name='mediasource', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_media_items_external_id'), 'media_items', ['external_id'], unique=True)
    op.create_index(op.f('ix_media_items_id'), 'media_items', ['id'], unique=False)

    op.create_table('queues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_queues_chat_id'), 'queues', ['chat_id'], unique=True)
    op.create_index(op.f('ix_queues_id'), 'queues', ['id'], unique=False)

    op.create_table('queue_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('queue_id', sa.Integer(), nullable=False),
        sa.Column('media_id', sa.Integer(), nullable=False),
        sa.Column('added_by', sa.BigInteger(), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'accepted', 'rejected', name='queueitemstatus', create_type=False), nullable=False),
        sa.Column('votes_for', sa.Integer(), nullable=True),
        sa.Column('votes_against', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['media_id'], ['media_items.id'], ),
        sa.ForeignKeyConstraint(['queue_id'], ['queues.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_queue_items_status', 'queue_items', ['status'], unique=False)
    op.create_index(op.f('ix_queue_items_id'), 'queue_items', ['id'], unique=False)
    op.create_index(op.f('ix_queue_items_queue_id'), 'queue_items', ['queue_id'], unique=False)

    op.create_table('votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('queue_item_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('vote_type', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['queue_item_id'], ['queue_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_votes_queue_item_user', 'votes', ['queue_item_id', 'user_id'], unique=True)
    op.create_index(op.f('ix_votes_id'), 'votes', ['id'], unique=False)

def downgrade():
    op.drop_table('votes')
    op.drop_table('queue_items')
    op.drop_table('queues')
    op.drop_table('media_items')
    op.execute("DROP TYPE IF EXISTS queueitemstatus")
    op.execute("DROP TYPE IF EXISTS mediasource")