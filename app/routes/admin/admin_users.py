from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.role import Role
from app.models.user import User
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["Admin - Utilisateurs"])
templates = Jinja2Templates(directory="app/templates")


def check_session(request: Request):
    if not request.state.user:
        return False
    return True


@router.get("/")
def admin_users_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    users = (
        db.query(User)
        .options(selectinload(User.roles))
        .order_by(User.fullname.is_(None), func.lower(User.fullname))
        .all()
    )

    return templates.TemplateResponse(
        "admin/users/list.html",
        {"request": request, "users": users},
    )


@router.get("/new")
def admin_user_new(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    roles = db.query(Role).order_by(Role.label).all()

    return templates.TemplateResponse(
        "admin/users/form.html",
        {
            "request": request,
            "action": "Créer",
            "user": None,
            "roles": roles,
            "user_role_names": set(),
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
    if not check_session(request):
        return RedirectResponse("/auth/login")

    user = db.query(User).options(selectinload(User.roles)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")

    return templates.TemplateResponse(
        "admin/users/detail.html",
        {"request": request, "user": user},
    )


@router.get("/{user_id}/edit")
def admin_user_edit(user_id: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    user = db.query(User).options(selectinload(User.roles)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")

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
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")

    role_objects = []
    if roles:
        role_objects = db.query(Role).filter(Role.name.in_(roles)).all()

    user.email = email
    user.fullname = fullname
    if password and password.strip():
        user.hashed_password = hash_password(password)
    user.roles = role_objects

    db.commit()

    return RedirectResponse(f"/admin/users/{user_id}", status_code=302)


@router.get("/{user_id}/delete")
def admin_user_delete(user_id: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Utilisateur non trouvé")

    user.roles = []
    db.delete(user)
    db.commit()

    return RedirectResponse("/admin/users", status_code=302)
