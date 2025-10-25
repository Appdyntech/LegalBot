"""create chat_history table"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'chat_history',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('chat_id', sa.String, nullable=False),
        sa.Column('session_id', sa.String, nullable=False),
        sa.Column('user_name', sa.String, nullable=True),
        sa.Column('question', sa.Text, nullable=False),
        sa.Column('answer', sa.Text, nullable=False),
        sa.Column('model', sa.String, nullable=True),
        sa.Column('confidence', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

def downgrade():
    op.drop_table('chat_history')
