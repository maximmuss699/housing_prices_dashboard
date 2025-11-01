import logging
from typing import Optional

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .models import User


logger = logging.getLogger("app.db")
# Prefer pbkdf2_sha256 for portability; allow verifying legacy bcrypt variants
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "bcrypt_sha256", "bcrypt"], deprecated="auto"
)

# Password hashing
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Password verification
def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

# Retrieve user by email from the database
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    logger.debug("db_query_get_user_by_email", extra={"email": email})
    user = db.query(User).filter(User.email == email).first()
    logger.debug(
        "db_query_result",
        extra={"found": bool(user), "entity": "User", "by": "email"},
    )
    return user

# Create a new user in the database
def create_user(db: Session, email: str, password: str) -> User:
    logger.info("db_insert_user_start", extra={"email": email})

    user = User(
        email=email,
        password_hash=hash_password(password),
    )

    db.add(user)
    db.commit()      # Persist to DB
    db.refresh(user) # To get the generated ID and other defaults

    logger.info("db_insert_user_done", extra={"user_id": user.id})
    return user

# List users with pagination
# For now it works for all logged in users only; in future may restrict to admins
def list_users(db: Session, offset: int = 0, limit: int = 100):
    logger.debug("db_query_list_users", extra={"offset": offset, "limit": limit})
    q = db.query(User).order_by(User.id.asc())
    if offset:
        q = q.offset(max(0, int(offset)))
    if limit:
        q = q.limit(max(1, min(int(limit), 500)))
    rows = q.all()
    logger.debug("db_query_result", extra={"count": len(rows), "entity": "User"})
    return rows
