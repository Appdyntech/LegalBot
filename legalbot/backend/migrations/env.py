import sys
import os
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context

# ==========================================
# 🧠 Ensure Alembic can import backend modules
# ==========================================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Import models for Alembic metadata
from legalbot.backend.app.models import Base

# ==========================================
# 🔧 Alembic Config
# ==========================================
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ==========================================
# 🧩 Database URL resolution
# ==========================================
DB_URL = os.getenv("DATABASE_URL")
if not DB_URL:
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Google%40123")  # URL-encoded '@'
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "34.93.244.73")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "legalbot")

    # 🔒 Escape '%' for configparser
    safe_password = POSTGRES_PASSWORD.replace('%', '%%')
    DB_URL = f"postgresql+psycopg2://{POSTGRES_USER}:{safe_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Apply final DB URL to Alembic
config.set_main_option("sqlalchemy.url", DB_URL.replace('%', '%%'))

# ==========================================
# 🧱 Metadata for migrations
# ==========================================
target_metadata = Base.metadata

# ==========================================
# 🚀 Migration functions
# ==========================================
def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    engine = create_engine(DB_URL, poolclass=pool.NullPool)

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
