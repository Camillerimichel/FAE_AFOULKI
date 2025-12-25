from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date

from app.authz import ADMIN_ROLES, has_any_role
from app.database import get_db
from app.models.parrainage import Parrainage
from app.models.parrain import Parrain
from app.models.filleule import Filleule

router = APIRouter(prefix="/parrainages", tags=["Admin - Parrainages"])
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
def admin_parrainages_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    parrainages = db.query(Parrainage).all()
    return templates.TemplateResponse(
        "admin/parrainages/list.html",
        {"request": request, "parrainages": parrainages},
    )


# --- CREER ---
@router.get("/new")
def admin_parrainage_new(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    parrains = db.query(Parrain).all()
    filleules = db.query(Filleule).all()

    return templates.TemplateResponse(
        "admin/parrainages/form.html",
        {
            "request": request,
            "action": "Créer",
            "parrainage": None,
            "parrains": parrains,
            "filleules": filleules,
        },
    )


@router.post("/new")
def admin_parrainage_create(
    request: Request,
    id_parrain: int = Form(...),
    id_filleule: int = Form(...),
    date_debut: str = Form(...),
    date_fin: str = Form(None),
    statut: str = Form(...),
    bourse_centre: int = Form(...),
    bourse_rw: int = Form(...),
    db: Session = Depends(get_db),
):
    obj = Parrainage(
        id_parrain=id_parrain,
        id_filleule=id_filleule,
        date_debut=date.fromisoformat(date_debut),
        date_fin=date.fromisoformat(date_fin) if date_fin else None,
        statut=statut,
        bourse_centre=bourse_centre,
        bourse_rw=bourse_rw,
    )

    db.add(obj)
    db.commit()

    return RedirectResponse("/admin/parrainages", status_code=302)


# --- DETAIL ---
@router.get("/{id_parrainage}")
def admin_parrainage_detail(id_parrainage: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    obj = db.query(Parrainage).filter(Parrainage.id_parrainage == id_parrainage).first()
    if not obj:
        raise HTTPException(404, "Parrainage non trouvé")

    return templates.TemplateResponse(
        "admin/parrainages/detail.html",
        {"request": request, "parrainage": obj},
    )


# --- EDITER ---
@router.get("/{id_parrainage}/edit")
def admin_parrainage_edit(id_parrainage: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    obj = db.query(Parrainage).filter(Parrainage.id_parrainage == id_parrainage).first()
    if not obj:
        raise HTTPException(404, "Parrainage non trouvé")

    parrains = db.query(Parrain).all()
    filleules = db.query(Filleule).all()

    return templates.TemplateResponse(
        "admin/parrainages/form.html",
        {
            "request": request,
            "action": "Modifier",
            "parrainage": obj,
            "parrains": parrains,
            "filleules": filleules,
        },
    )


@router.post("/{id_parrainage}/edit")
def admin_parrainage_update(
    id_parrainage: int,
    request: Request,
    id_parrain: int = Form(...),
    id_filleule: int = Form(...),
    date_debut: str = Form(...),
    date_fin: str = Form(None),
    statut: str = Form(...),
    bourse_centre: int = Form(...),
    bourse_rw: int = Form(...),
    db: Session = Depends(get_db),
):

    obj = db.query(Parrainage).filter(Parrainage.id_parrainage == id_parrainage).first()
    if not obj:
        raise HTTPException(404, "Parrainage non trouvé")

    obj.id_parrain = id_parrain
    obj.id_filleule = id_filleule
    obj.date_debut = date.fromisoformat(date_debut)
    obj.date_fin = date.fromisoformat(date_fin) if date_fin else None
    obj.statut = statut
    obj.bourse_centre = bourse_centre
    obj.bourse_rw = bourse_rw

    db.commit()

    return RedirectResponse(f"/admin/parrainages/{id_parrainage}", status_code=302)


# --- DELETE ---
@router.get("/{id_parrainage}/delete")
def admin_parrainage_delete(id_parrainage: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    obj = db.query(Parrainage).filter(Parrainage.id_parrainage == id_parrainage).first()
    if not obj:
        raise HTTPException(404, "Parrainage non trouvé")

    db.delete(obj)
    db.commit()

    return RedirectResponse("/admin/parrainages", status_code=302)
