from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Float, ForeignKey
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB

from .db import Base, engine


# User model representing users table in the database
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


def _json_type():
    try:
        if engine.url.get_backend_name().startswith("postgres"):
            return PG_JSONB
    except Exception:
        pass
    return SQLITE_JSON


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payload = Column(_json_type(), nullable=False)
    predicted_value = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
