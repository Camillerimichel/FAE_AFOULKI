from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.authz import ADMIN_ROLES, has_any_role
from app.database import get_db
from app.models.annee_scolaire import AnneeScolaire

router = APIRouter(prefix="/annees-scolaires", tags=["Admin - Années scolaires"])
templates = Jinja2Templates(directory="app/templates")


def check_session(request: Request):
    if not request.state.user:
        return False
    if not has_any_role(request, ADMIN_ROLES):
        raise HTTPException(403, "Accès refusé")
    return True


def _build_periode(start_year: int) -> str:
    return f"{start_year}/{start_year + 1}"


def _normalize_year(value: str) -> int:
    try:
        year = int(value)
    except (TypeError, ValueError):
        raise HTTPException(400, "Année invalide")
    if year < 1000 or year > 9999:
        raise HTTPException(400, "Année invalide")
    return year


def _start_year_from_periode(periode: str) -> str:
    if not periode:
        return ""
    return periode.split("/", 1)[0]


@router.get("/")
def admin_annees_scolaires_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    annees = db.query(AnneeScolaire).order_by(AnneeScolaire.periode).all()

    return templates.TemplateResponse(
        "admin/annees_scolaires/list.html",
        {"request": request, "annees": annees},
    )


@router.get("/new")
def admin_annees_scolaires_new(request: Request):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    return templates.TemplateResponse(
        "admin/annees_scolaires/form.html",
        {
            "request": request,
            "action": "Créer",
            "annee_scolaire": None,
            "annee_debut": "",
            "periode_preview": "AAAA/AAAA+1",
        },
    )


@router.post("/new")
def admin_annees_scolaires_create(
    request: Request,
    annee_debut: str = Form(...),
    db: Session = Depends(get_db),
):
    start_year = _normalize_year(annee_debut)
    periode = _build_periode(start_year)

    annee = AnneeScolaire(periode=periode)
    db.add(annee)
    db.commit()

    return RedirectResponse("/admin/annees-scolaires", status_code=302)


@router.get("/{id_annee_scolaire}")
def admin_annees_scolaires_detail(
    id_annee_scolaire: int,
    request: Request,
    db: Session = Depends(get_db),
):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    annee = (
        db.query(AnneeScolaire)
        .filter(AnneeScolaire.id_annee_scolaire == id_annee_scolaire)
        .first()
    )
    if not annee:
        raise HTTPException(404, "Année scolaire non trouvée")

    return templates.TemplateResponse(
        "admin/annees_scolaires/detail.html",
        {"request": request, "annee": annee},
    )


@router.get("/{id_annee_scolaire}/edit")
def admin_annees_scolaires_edit(
    id_annee_scolaire: int,
    request: Request,
    db: Session = Depends(get_db),
):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    annee = (
        db.query(AnneeScolaire)
        .filter(AnneeScolaire.id_annee_scolaire == id_annee_scolaire)
        .first()
    )
    if not annee:
        raise HTTPException(404, "Année scolaire non trouvée")

    annee_debut = _start_year_from_periode(annee.periode)
    periode_preview = (
        _build_periode(int(annee_debut)) if annee_debut.isdigit() else "AAAA/AAAA+1"
    )

    return templates.TemplateResponse(
        "admin/annees_scolaires/form.html",
        {
            "request": request,
            "action": "Modifier",
            "annee_scolaire": annee,
            "annee_debut": annee_debut,
            "periode_preview": periode_preview,
        },
    )


@router.post("/{id_annee_scolaire}/edit")
def admin_annees_scolaires_update(
    id_annee_scolaire: int,
    request: Request,
    annee_debut: str = Form(...),
    db: Session = Depends(get_db),
):
    annee = (
        db.query(AnneeScolaire)
        .filter(AnneeScolaire.id_annee_scolaire == id_annee_scolaire)
        .first()
    )
    if not annee:
        raise HTTPException(404, "Année scolaire non trouvée")

    start_year = _normalize_year(annee_debut)
    annee.periode = _build_periode(start_year)
    db.commit()

    return RedirectResponse(f"/admin/annees-scolaires/{id_annee_scolaire}", status_code=302)


@router.get("/{id_annee_scolaire}/delete")
def admin_annees_scolaires_delete(
    id_annee_scolaire: int,
    request: Request,
    db: Session = Depends(get_db),
):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    annee = (
        db.query(AnneeScolaire)
        .filter(AnneeScolaire.id_annee_scolaire == id_annee_scolaire)
        .first()
    )
    if not annee:
        raise HTTPException(404, "Année scolaire non trouvée")

    db.delete(annee)
    db.commit()

    return RedirectResponse("/admin/annees-scolaires", status_code=302)
