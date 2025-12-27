from datetime import datetime

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.security import hash_password, verify_password
from app.services.email_service import send_email
from app.services.password_reset_service import (
    clear_user_reset_token,
    hash_reset_token,
    set_user_reset_token,
    verify_user_reset_token,
)

router = APIRouter(prefix="/auth", tags=["Auth HTML"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login")
def login_page(request: Request):
    """
    Affiche la page de connexion HTML
    """
    info = None
    if request.query_params.get("reset") == "success":
        info = "Votre mot de passe a bien été mis à jour."
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None, "info": info}
    )


@router.post("/login")
def login_submit(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(...),
    password: str = Form(...),
):
    """
    Vérifie l'utilisateur dans la base + crée un cookie de session
    """
    user = db.query(User).filter(User.email == email).first()

    # Vérification email + mot de passe
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Email ou mot de passe incorrect"
            },
        )

    # Login OK → création cookie session
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(
        key="session",
        value=str(user.id),
        httponly=True,
        max_age=86400,       # 24h
    )
    return response


@router.get("/logout")
def logout(request: Request):
    """
    Supprime la session actuelle
    """
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("session")
    return response


@router.get("/forgot-password")
def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        "forgot_password.html",
        {"request": request, "error": None, "info": None},
    )


@router.post("/forgot-password")
def forgot_password_submit(
    request: Request,
    db: Session = Depends(get_db),
    email: str = Form(...),
):
    user = db.query(User).filter(User.email == email).first()
    if user:
        token = set_user_reset_token(user)
        db.commit()
        base_url = str(request.base_url).rstrip("/")
        reset_link = f"{base_url}/auth/reset-password?token={token}"
        subject = "Réinitialiser votre mot de passe"
        body = (
            "Bonjour,\n\n"
            "Vous avez demandé la réinitialisation de votre mot de passe.\n"
            "Cliquez sur le lien suivant pour définir un nouveau mot de passe :\n"
            f"{reset_link}\n\n"
            "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.\n"
        )
        ok, err = send_email(user.email, subject, body)
        if not ok:
            print(f"[password-reset] email non envoye pour {user.email}: {err}")

    return templates.TemplateResponse(
        "forgot_password.html",
        {
            "request": request,
            "error": None,
            "info": "Si un compte existe, un email de reinitialisation a ete envoye.",
        },
    )


@router.get("/reset-password")
def reset_password_page(
    request: Request,
    token: str | None = None,
    db: Session = Depends(get_db),
):
    user = None
    token_valid = False
    if token:
        token_hash = hash_reset_token(token)
        user = db.query(User).filter(User.reset_token_hash == token_hash).first()
        token_valid = verify_user_reset_token(user, token)

        if user and user.reset_token_expires and user.reset_token_expires < datetime.utcnow():
            clear_user_reset_token(user)
            db.commit()

    return templates.TemplateResponse(
        "reset_password.html",
        {
            "request": request,
            "error": None,
            "token": token,
            "token_valid": token_valid,
        },
    )


@router.post("/reset-password")
def reset_password_submit(
    request: Request,
    db: Session = Depends(get_db),
    token: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    token_hash = hash_reset_token(token)
    user = db.query(User).filter(User.reset_token_hash == token_hash).first()

    if not verify_user_reset_token(user, token):
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "error": "Lien invalide ou expiré.",
                "token": token,
                "token_valid": False,
            },
        )

    if not password or password != password_confirm:
        return templates.TemplateResponse(
            "reset_password.html",
            {
                "request": request,
                "error": "Les mots de passe ne correspondent pas.",
                "token": token,
                "token_valid": True,
            },
        )

    user.hashed_password = hash_password(password)
    clear_user_reset_token(user)
    db.commit()

    return RedirectResponse("/auth/login?reset=success", status_code=302)
