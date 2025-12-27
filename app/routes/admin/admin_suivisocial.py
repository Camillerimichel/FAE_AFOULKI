from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.suivisocial import SuiviSocial
from app.models.filleule import Filleule

router = APIRouter(prefix="/suivisocial", tags=["Admin - Suivi social"])
templates = Jinja2Templates(directory="app/templates")


# --- Vérification session ---
def check_session(request: Request):
    if not request.state.user:
        return False
    return True


# --- LISTE ---
@router.get("/")
def admin_suivis_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    suivis = db.query(SuiviSocial).all()

    return templates.TemplateResponse(
        "admin/suivisocial/list.html",
        {"request": request, "suivis": suivis},
    )


# --- NOUVEAU ---
@router.get("/new")
def admin_suivi_new(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    filleules = db.query(Filleule).all()

    return templates.TemplateResponse(
        "admin/suivisocial/form.html",
        {"request": request, "action": "Créer", "suivi": None, "filleules": filleules},
    )


@router.post("/new")
def admin_suivi_create(
    request: Request,
    id_filleule: int = Form(...),
    date_suivi: str = Form(...),
    commentaire: str = Form(...),
    besoins: str = Form(...),
    db: Session = Depends(get_db),
):
    s = SuiviSocial(
        id_filleule=id_filleule,
        date_suivi=date_suivi,
        commentaire=commentaire,
        besoins=besoins,
    )

    db.add(s)
    db.commit()

    return RedirectResponse("/admin/suivisocial", status_code=302)


# --- DETAIL ---
@router.get("/{id_suivi}")
def admin_suivi_detail(id_suivi: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    s = db.query(SuiviSocial).filter(SuiviSocial.id_suivi == id_suivi).first()
    if not s:
        raise HTTPException(404, "Suivi non trouvé")

    return templates.TemplateResponse(
        "admin/suivisocial/detail.html",
        {"request": request, "s": s},
    )


# --- EDIT ---
@router.get("/{id_suivi}/edit")
def admin_suivi_edit(id_suivi: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    s = db.query(SuiviSocial).filter(SuiviSocial.id_suivi == id_suivi).first()
    if not s:
        raise HTTPException(404, "Suivi non trouvé")

    filleules = db.query(Filleule).all()

    return templates.TemplateResponse(
        "admin/suivisocial/form.html",
        {"request": request, "action": "Modifier", "suivi": s, "filleules": filleules},
    )


@router.post("/{id_suivi}/edit")
def admin_suivi_update(
    id_suivi: int,
    request: Request,
    id_filleule: int = Form(...),
    date_suivi: str = Form(...),
    commentaire: str = Form(...),
    besoins: str = Form(...),
    db: Session = Depends(get_db),
):
    s = db.query(SuiviSocial).filter(SuiviSocial.id_suivi == id_suivi).first()
    if not s:
        raise HTTPException(404, "Suivi non trouvé")

    s.id_filleule = id_filleule
    s.date_suivi = date_suivi
    s.commentaire = commentaire
    s.besoins = besoins

    db.commit()

    return RedirectResponse(f"/admin/suivisocial/{id_suivi}", status_code=302)


# --- DELETE ---
@router.get("/{id_suivi}/delete")
def admin_suivi_delete(id_suivi: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    s = db.query(SuiviSocial).filter(SuiviSocial.id_suivi == id_suivi).first()
    if not s:
        raise HTTPException(404, "Suivi non trouvé")

    db.delete(s)
    db.commit()

    return RedirectResponse("/admin/suivisocial", status_code=302)
