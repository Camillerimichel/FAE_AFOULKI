from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.authz import USER_ADMIN_ROLES, has_any_role
from app.database import get_db
from app.models.user import User
from app.models.user_connection_log import UserConnectionLog

router = APIRouter(prefix="/connexions", tags=["Admin - Connexions"])
templates = Jinja2Templates(directory="app/templates")


def require_admin(request: Request):
    if not request.state.user:
        return RedirectResponse("/auth/login")
    if not has_any_role(request, USER_ADMIN_ROLES):
        raise HTTPException(403, "Acces interdit")
    return None


@router.get("/")
def admin_connexions_list(request: Request, db: Session = Depends(get_db)):
    redirect = require_admin(request)
    if redirect:
        return redirect

    logs = (
        db.query(UserConnectionLog)
        .join(User)
        .options(selectinload(UserConnectionLog.user))
        .order_by(
            User.fullname.is_(None),
            func.lower(User.fullname),
            User.id,
            UserConnectionLog.created_at.desc(),
        )
        .all()
    )

    grouped = []
    for log in logs:
        user = log.user
        label = user.fullname or user.email
        if not grouped or grouped[-1]["user_id"] != user.id:
            grouped.append({"user_id": user.id, "user_label": label, "dates": []})
        date_key = log.created_at.date() if log.created_at else None
        if not grouped[-1]["dates"] or grouped[-1]["dates"][-1]["date"] != date_key:
            grouped[-1]["dates"].append({"date": date_key, "entries": []})
        grouped[-1]["dates"][-1]["entries"].append(log)

    return templates.TemplateResponse(
        "admin/connexions/list.html",
        {"request": request, "groups": grouped},
    )
