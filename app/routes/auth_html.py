from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth HTML"])
templates = Jinja2Templates(directory="app/templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str):
    """
    Vérifie le mot de passe utilisateur avec bcrypt
    """
    return pwd_context.verify(plain_password, hashed_password)


@router.get("/login")
def login_page(request: Request):
    """
    Affiche la page de connexion HTML
    """
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None}
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
