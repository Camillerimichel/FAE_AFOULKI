from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.database import SessionLocal, DB_NAME
from app.models.user import User


class SessionMiddleware(BaseHTTPMiddleware):
    def _load_legacy_role_name(self, db: Session, user_id: int) -> str | None:
        has_column = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = :db
                  AND TABLE_NAME = 'users'
                  AND COLUMN_NAME = 'user_role'
                """
            ),
            {"db": DB_NAME},
        ).scalar()
        if not has_column:
            return None

        role_id = db.execute(
            text("SELECT user_role FROM users WHERE id = :id"),
            {"id": user_id},
        ).scalar()
        if not role_id:
            return None

        return db.execute(
            text("SELECT name FROM roles WHERE id = :id"),
            {"id": role_id},
        ).scalar()

    async def dispatch(self, request, call_next):
        request.state.user = None
        request.state.user_roles = set()

        session_cookie = request.cookies.get("session")

        if session_cookie:
            db: Session | None = None
            try:
                db = SessionLocal()
                user = db.query(User).options(selectinload(User.roles)).filter(User.id == int(session_cookie)).first()
                request.state.user = user
                if user:
                    request.state.user_roles = {role.name for role in user.roles}
                    if not request.state.user_roles:
                        try:
                            legacy_name = self._load_legacy_role_name(db, user.id)
                        except Exception:
                            legacy_name = None
                        if legacy_name:
                            request.state.user_roles = {legacy_name}
            except:
                request.state.user = None
                request.state.user_roles = set()
            finally:
                if db:
                    db.close()

        return await call_next(request)
