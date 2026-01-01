from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.database import SessionLocal, DB_NAME
from app.models.user import User
from app.models.user_connection_log import UserConnectionLog


class SessionMiddleware(BaseHTTPMiddleware):
    def _get_client_ip(self, request) -> str | None:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return None

    def _should_log_request(self, request) -> bool:
        if request.method != "GET":
            return False
        path = request.url.path
        if path.startswith(("/static", "/Documents", "/admin/api")):
            return False
        if path in {"/favicon.ico", "/apple-touch-icon.png", "/apple-touch-icon-precomposed.png"}:
            return False
        return True

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

        response = await call_next(request)

        if request.state.user and self._should_log_request(request):
            db = None
            try:
                db = SessionLocal()
                path = request.url.path
                if request.url.query:
                    path = f"{path}?{request.url.query}"
                log_entry = UserConnectionLog(
                    user_id=request.state.user.id,
                    ip_address=self._get_client_ip(request),
                    path=path,
                )
                db.add(log_entry)
                db.commit()
            except Exception:
                if db:
                    db.rollback()
            finally:
                if db:
                    db.close()

        return response
