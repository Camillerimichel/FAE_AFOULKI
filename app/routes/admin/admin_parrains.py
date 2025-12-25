from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.authz import ADMIN_ROLES, has_any_role
from app.database import get_db
from app.models.parrain import Parrain

router = APIRouter(prefix="/parrains", tags=["Admin - Parrains"])
templates = Jinja2Templates(directory="app/templates")


# --- Vérification session ---
def check_session(request: Request):
    if not request.state.user:
        return False
    if not has_any_role(request, ADMIN_ROLES):
        raise HTTPException(403, "Accès refusé")
    return True


# --- LISTE ---
@router.get("/")
def admin_parrains_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    parrains = db.query(Parrain).all()

    return templates.TemplateResponse(
        "admin/parrains/list.html",
        {"request": request, "parrains": parrains},
    )


# --- CREER ---
@router.get("/new")
def admin_parrain_new(request: Request):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    return templates.TemplateResponse(
        "admin/parrains/form.html",
        {"request": request, "action": "Créer", "parrain": None},
    )


@router.post("/new")
def admin_parrain_create(
    request: Request,
    nom: str = Form(...),
    prenom: str = Form(...),
    telephone: str = Form(...),
    email: str = Form(...),
    adresse: str = Form(...),
    db: Session = Depends(get_db),
):
    parrain = Parrain(
        nom=nom,
        prenom=prenom,
        telephone=telephone,
        email=email,
        adresse=adresse,
    )
    db.add(parrain)
    db.commit()

    return RedirectResponse("/admin/parrains", status_code=302)


# --- DETAIL ---
@router.get("/{parrain_id}")
def admin_parrain_detail(parrain_id: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    parrain = db.query(Parrain).filter(Parrain.id_parrain == parrain_id).first()
    if not parrain:
        raise HTTPException(404, "Parrain non trouvé")

    return templates.TemplateResponse(
        "admin/parrains/detail.html",
        {"request": request, "parrain": parrain},
    )


# --- EDITER ---
@router.get("/{parrain_id}/edit")
def admin_parrain_edit(parrain_id: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    parrain = db.query(Parrain).filter(Parrain.id_parrain == parrain_id).first()
    if not parrain:
        raise HTTPException(404, "Parrain non trouvé")

    return templates.TemplateResponse(
        "admin/parrains/form.html",
        {"request": request, "action": "Modifier", "parrain": parrain},
    )


@router.post("/{parrain_id}/edit")
def admin_parrain_update(
    parrain_id: int,
    request: Request,
    nom: str = Form(...),
    prenom: str = Form(...),
    telephone: str = Form(...),
    email: str = Form(...),
    adresse: str = Form(...),
    db: Session = Depends(get_db),
):
    parrain = db.query(Parrain).filter(Parrain.id_parrain == parrain_id).first()
    if not parrain:
        raise HTTPException(404, "Parrain non trouvé")

    parrain.nom = nom
    parrain.prenom = prenom
    parrain.telephone = telephone
    parrain.email = email
    parrain.adresse = adresse

    db.commit()

    return RedirectResponse(f"/admin/parrains/{parrain_id}", status_code=302)


# --- DELETE ---
@router.get("/{parrain_id}/delete")
def admin_parrain_delete(parrain_id: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    parrain = db.query(Parrain).filter(Parrain.id_parrain == parrain_id).first()
    if not parrain:
        raise HTTPException(404, "Parrain non trouvé")

    db.delete(parrain)
    db.commit()

    return RedirectResponse("/admin/parrains", status_code=302)
