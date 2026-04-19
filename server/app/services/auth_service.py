from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User
from app.utils.security import hash_password, verify_password


def ensure_default_user(db: Session) -> User:
    settings = get_settings()
    user = db.scalar(select(User).where(User.username == settings.default_username))
    if user:
        return user
    user = User(
        username=settings.default_username,
        password_hash=hash_password(settings.default_password),
        display_name=settings.default_display_name,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.username == username))
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
