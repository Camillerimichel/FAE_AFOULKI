from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.authz import USER_ADMIN_ROLES, USER_VIEW_ROLES, has_any_role
from app.database import get_db
from app.models.role import Role
from app.models.user import User
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["Admin - Utilisateurs"])
templates = Jinja2Templates(directory="app/templates")

ADMIN_ROLE_NAME = "administrateur"


def require_user_view(request: Request):
    if not request.state.user:
        return RedirectResponse("/auth/login")
    if not has_any_role(request, USER_VIEW_ROLES):
        raise HTTPException(403, "Acces interdit")
    return None


def require_user_admin(request: Request):
    if not request.state.user:
        return RedirectResponse("/auth/login")
    if not has_any_role(request, USER_ADMIN_ROLES):
        raise HTTPException(403, "Acces interdit")
    return None


def is_admin_user(user: User) -> bool:
    return any(role.name == ADMIN_ROLE_NAME for role in user.roles)


@router.get("/")
def admin_users_list(request: Request, db: Session = Depends(get_db)):
    redirect = require_user_view(request)
    if redirect:
        return redirect

    users = (
        db.query(User)
        .options(selectinload(User.roles))
        .order_by(User.fullname.is_(None), func.lower(User.fullname))
        .all()
    )

    return templates.TemplateResponse(
        "admin/users/list.html",
        {
            "request": request,
            "users": users,
            "can_admin_users": has_any_role(request, USER_ADMIN_ROLES),
        },
    )


@router.get("/new")
def admin_user_new(request: Request, db: Session = Depends(get_db)):
    redirect = require_user_admin(request)
    if redirect:
        return redirect

    roles = db.query(Role).order_by(Role.label).all()

    return templates.TemplateResponse(
        "admin/users/form.html",
        {
            "request": request,
            "action": "Créer",
            "user": None,
            "roles": roles,
            "user_role_names": set(),
            "can_edit_roles": True,
        },
    )


@router.post("/new")
def admin_user_create(
    request: Request,
    email: str = Form(...),
    fullname: str = Form(None),
    password: str = Form(...),
    roles: list[str] = Form([]),
    db: Session = Depends(get_db),
):
    redirect = require_user_admin(request)
    if redirect:
        return redirect
    role_objects = []
    if roles:
        role_objects = db.query(Role).filter(Role.name.in_(roles)).all()

    user = User(
        email=email,
        fullname=fullname,
        hashed_password=hash_password(password),
    )
    user.roles = role_objects
    db.add(user)
    db.commit()

    return RedirectResponse("/admin/users", status_code=302)


@router.get("/{user_id}")
def admin_user_detail(user_id: int, request: Request, db: Session = Depends(get_db)):
    redirect = require_user_view(request)
    if redirect:
        return redirect

    user = db.query(User).options(selectinload(User.roles)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")

    is_admin_target = is_admin_user(user)
    can_edit_user = has_any_role(request, USER_ADMIN_ROLES) or not is_admin_target

    return templates.TemplateResponse(
        "admin/users/detail.html",
        {
            "request": request,
            "user": user,
            "can_admin_users": has_any_role(request, USER_ADMIN_ROLES),
            "can_edit_user": can_edit_user,
        },
    )


@router.get("/{user_id}/edit")
def admin_user_edit(user_id: int, request: Request, db: Session = Depends(get_db)):
    redirect = require_user_view(request)
    if redirect:
        return redirect

    user = db.query(User).options(selectinload(User.roles)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")
    if is_admin_user(user) and not has_any_role(request, USER_ADMIN_ROLES):
        raise HTTPException(403, "Acces interdit")

    roles = db.query(Role).order_by(Role.label).all()
    user_role_names = {role.name for role in user.roles}

    return templates.TemplateResponse(
        "admin/users/form.html",
        {
            "request": request,
            "action": "Modifier",
            "user": user,
            "roles": roles,
            "user_role_names": user_role_names,
            "can_edit_roles": has_any_role(request, USER_ADMIN_ROLES),
        },
    )


@router.post("/{user_id}/edit")
def admin_user_update(
    user_id: int,
    request: Request,
    email: str = Form(...),
    fullname: str = Form(None),
    password: str = Form(None),
    roles: list[str] = Form([]),
    db: Session = Depends(get_db),
):
    redirect = require_user_view(request)
    if redirect:
        return redirect
    is_admin = has_any_role(request, USER_ADMIN_ROLES)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")
    if is_admin_user(user) and not is_admin:
        raise HTTPException(403, "Acces interdit")

    user.email = email
    user.fullname = fullname
    if password and password.strip():
        user.hashed_password = hash_password(password)
    if is_admin:
        role_objects = []
        if roles:
            role_objects = db.query(Role).filter(Role.name.in_(roles)).all()
        user.roles = role_objects

    db.commit()

    return RedirectResponse(f"/admin/users/{user_id}", status_code=302)


@router.get("/{user_id}/delete")
def admin_user_delete(user_id: int, request: Request, db: Session = Depends(get_db)):
    redirect = require_user_admin(request)
    if redirect:
        return redirect

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")

    user.roles = []
    db.delete(user)
    db.commit()

    return RedirectResponse("/admin/users", status_code=302)
