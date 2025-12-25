from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.authz import ADMIN_ROLES, has_any_role
from app.database import get_db
from app.models.correspondant import Correspondant
from app.models.filleule import Filleule

router = APIRouter(prefix="/correspondants", tags=["Admin - Correspondants"])
templates = Jinja2Templates(directory="app/templates")


# --- Vérification session ---
def check_session(request: Request):
    if not request.state.user:
        return False
    if not has_any_role(request, ADMIN_ROLES):
        raise HTTPException(403, "Accès refusé")
    return True


# --- LISTE DES CORRESPONDANTS ---
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

    filleules = db.query(Filleule).all()

    return templates.TemplateResponse(
        "admin/correspondants/form.html",
        {"request": request, "action": "Créer", "correspondant": None, "filleules": filleules},
    )


@router.post("/new")
def admin_correspondant_create(
    request: Request,
    id_filleule: int = Form(...),
    nom: str = Form(...),
    prenom: str = Form(...),
    telephone: str = Form(...),
    email: str = Form(...),
    lien: str = Form(...),
    db: Session = Depends(get_db),
):
    c = Correspondant(
        id_filleule=id_filleule,
        nom=nom,
        prenom=prenom,
        telephone=telephone,
        email=email,
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
        raise HTTPException(404, "Correspondant non trouvé")

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
        raise HTTPException(404, "Correspondant non trouvé")

    filleules = db.query(Filleule).all()

    return templates.TemplateResponse(
        "admin/correspondants/form.html",
        {"request": request, "action": "Modifier", "correspondant": c, "filleules": filleules},
    )


@router.post("/{id_correspondant}/edit")
def admin_correspondant_update(
    id_correspondant: int,
    request: Request,
    id_filleule: int = Form(...),
    nom: str = Form(...),
    prenom: str = Form(...),
    telephone: str = Form(...),
    email: str = Form(...),
    lien: str = Form(...),
    db: Session = Depends(get_db),
):
    c = db.query(Correspondant).filter(Correspondant.id_correspondant == id_correspondant).first()
    if not c:
        raise HTTPException(404, "Correspondant non trouvé")

    c.id_filleule = id_filleule
    c.nom = nom
    c.prenom = prenom
    c.telephone = telephone
    c.email = email
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
        raise HTTPException(404, "Correspondant non trouvé")

    db.delete(c)
    db.commit()

    return RedirectResponse("/admin/correspondants", status_code=302)
