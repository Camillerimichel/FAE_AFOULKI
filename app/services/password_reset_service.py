import hashlib
import os
import secrets
from datetime import datetime, timedelta

from app.models.user import User

DEFAULT_TTL_MINUTES = int(os.getenv("RESET_TOKEN_TTL_MINUTES", "120"))


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_reset_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    return token, _hash_token(token)


def set_user_reset_token(user: User, ttl_minutes: int | None = None) -> str:
    token, token_hash = generate_reset_token()
    user.reset_token_hash = token_hash
    user.reset_token_expires = datetime.utcnow() + timedelta(minutes=ttl_minutes or DEFAULT_TTL_MINUTES)
    return token


def verify_user_reset_token(user: User | None, token: str | None) -> bool:
    if not user or not token:
        return False
    if not user.reset_token_hash or not user.reset_token_expires:
        return False
    if user.reset_token_expires < datetime.utcnow():
        return False
    return _hash_token(token) == user.reset_token_hash


def clear_user_reset_token(user: User) -> None:
    user.reset_token_hash = None
    user.reset_token_expires = None


def hash_reset_token(token: str) -> str:
    return _hash_token(token)
