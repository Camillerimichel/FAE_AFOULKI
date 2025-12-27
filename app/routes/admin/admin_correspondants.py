from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.correspondant import Correspondant

router = APIRouter(prefix="/correspondants", tags=["Admin - Référents"])
templates = Jinja2Templates(directory="app/templates")


def normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


# --- Vérification session ---
def check_session(request: Request):
    if not request.state.user:
        return False
    return True


# --- LISTE DES RÉFÉRENTS ---
@router.get("/")
def admin_correspondants_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    correspondants = db.query(Correspondant).all()
    return templates.TemplateResponse(
        "admin/correspondants/list.html",
        {"request": request, "correspondants": correspondants},
    )


# --- FORMULAIRE NOUVEAU ---
@router.get("/new")
def admin_correspondant_new(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    return templates.TemplateResponse(
        "admin/correspondants/form.html",
        {"request": request, "action": "Créer", "correspondant": None},
    )


@router.post("/new")
def admin_correspondant_create(
    request: Request,
    nom: str = Form(...),
    prenom: str = Form(...),
    telephone: str | None = Form(None),
    email: str | None = Form(None),
    lien: str = Form(...),
    db: Session = Depends(get_db),
):
    c = Correspondant(
        nom=nom,
        prenom=prenom,
        telephone=normalize_optional(telephone),
        email=normalize_optional(email),
        lien=lien,
    )

    db.add(c)
    db.commit()

    return RedirectResponse("/admin/correspondants", status_code=302)


# --- DÉTAIL ---
@router.get("/{id_correspondant}")
def admin_correspondant_detail(id_correspondant: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    c = db.query(Correspondant).filter(Correspondant.id_correspondant == id_correspondant).first()
    if not c:
        raise HTTPException(404, "Référent non trouvé")

    return templates.TemplateResponse(
        "admin/correspondants/detail.html",
        {"request": request, "c": c},
    )


# --- EDIT ---
@router.get("/{id_correspondant}/edit")
def admin_correspondant_edit(id_correspondant: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    c = db.query(Correspondant).filter(Correspondant.id_correspondant == id_correspondant).first()
    if not c:
        raise HTTPException(404, "Référent non trouvé")

    return templates.TemplateResponse(
        "admin/correspondants/form.html",
        {"request": request, "action": "Modifier", "correspondant": c},
    )


@router.post("/{id_correspondant}/edit")
def admin_correspondant_update(
    id_correspondant: int,
    request: Request,
    nom: str = Form(...),
    prenom: str = Form(...),
    telephone: str | None = Form(None),
    email: str | None = Form(None),
    lien: str = Form(...),
    db: Session = Depends(get_db),
):
    c = db.query(Correspondant).filter(Correspondant.id_correspondant == id_correspondant).first()
    if not c:
        raise HTTPException(404, "Référent non trouvé")

    c.nom = nom
    c.prenom = prenom
    c.telephone = normalize_optional(telephone)
    c.email = normalize_optional(email)
    c.lien = lien

    db.commit()

    return RedirectResponse(f"/admin/correspondants/{id_correspondant}", status_code=302)


# --- DELETE ---
@router.get("/{id_correspondant}/delete")
def admin_correspondant_delete(id_correspondant: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    c = db.query(Correspondant).filter(Correspondant.id_correspondant == id_correspondant).first()
    if not c:
        raise HTTPException(404, "Référent non trouvé")

    db.delete(c)
    db.commit()

    return RedirectResponse("/admin/correspondants", status_code=302)
