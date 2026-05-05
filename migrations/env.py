from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os

# this is the Alembic Config object, which provides
# the values of the alembic.ini file, which is read
# by the main alembic commands.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except FileNotFoundError:
        # alembic.ini is in the parent directory, not in migrations/
        pass

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
from WebApp import create_app, db

app = create_app()
target_metadata = db.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get the database URI from the Flask app
    sqlalchemy_url = app.config.get("SQLALCHEMY_DATABASE_URI")
    
    if not sqlalchemy_url:
        sqlalchemy_url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    
    if not sqlalchemy_url:
        configuration = config.get_section(config.config_ini_section)
        sqlalchemy_url = configuration.get("sqlalchemy.url")
    
    if not sqlalchemy_url:
        raise ValueError("No database URL configured. Set DATABASE_URL or SQLALCHEMY_DATABASE_URI.")

    connectable = engine_from_config(
        {"sqlalchemy.url": sqlalchemy_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
