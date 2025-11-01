import os
import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("app.db")

# Require Postgres DATABASE_URL; fail fast if missing
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Expected Postgres URL like "
        "postgresql+psycopg2://app:app@db:5432/appdb"
    )

# Create engine / session factory
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

safe_url = engine.url.render_as_string(hide_password=True)
logger.info("db_engine_created", extra={"url": safe_url})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Initialize the database (create tables)
# Import models to ensure they are registered with Base
# This is idempotent; will not drop existing tables
def init_db() -> None:
    from . import models  # noqa: F401 - ensure models are imported
    logger.info("db_init_start", extra={"url": safe_url})
    Base.metadata.create_all(bind=engine)
    logger.info("db_init_complete")

# Provide a transactional scope around a series of operations
# Open a session, yield it, commit if successful, rollback on error, and close
@contextmanager
def session_scope() -> Generator:

    db = SessionLocal()
    logger.debug("db_session_open")
    try:
        yield db
        db.commit()
        logger.debug("db_session_commit")
    except Exception:
        logger.exception("db_session_rollback")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("db_session_close")

# FastAPI dependency to get DB session per request
def get_db() -> Generator:
    db = SessionLocal()
    logger.debug("db_session_open")
    try:
        yield db
    finally:
        db.close()
        logger.debug("db_session_close")


@event.listens_for(engine, "connect")
def _on_connect(dbapi_connection, connection_record):
    logger.info("db_connect")


@event.listens_for(engine, "engine_connect")
def _on_engine_connect(connection):
    logger.debug("db_engine_connect")
