from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session, selectinload

from app.database import SessionLocal
from app.models.user import User


class SessionMiddleware(BaseHTTPMiddleware):
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
            except:
                request.state.user = None
                request.state.user_roles = set()
            finally:
                if db:
                    db.close()

        return await call_next(request)
