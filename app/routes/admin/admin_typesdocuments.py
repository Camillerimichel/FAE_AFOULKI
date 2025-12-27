from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.typedocument import TypeDocument

router = APIRouter(prefix="/typesdocuments", tags=["Admin - Types de documents"])
templates = Jinja2Templates(directory="app/templates")


# --- Vérification session ---
def check_session(request: Request):
    if not request.state.user:
        return False
    return True


# --- LISTE ---
@router.get("/")
def admin_typesdocuments_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    typesdocs = db.query(TypeDocument).all()

    return templates.TemplateResponse(
        "admin/typesdocuments/list.html",
        {"request": request, "typesdocs": typesdocs},
    )


# --- NOUVEAU ---
@router.get("/new")
def admin_typesdocuments_new(request: Request):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    return templates.TemplateResponse(
        "admin/typesdocuments/form.html",
        {"request": request, "action": "Créer", "type_document": None},
    )


@router.post("/new")
def admin_typesdocuments_create(
    request: Request,
    libelle: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
):
    t = TypeDocument(libelle=libelle, description=description)
    db.add(t)
    db.commit()

    return RedirectResponse("/admin/typesdocuments", status_code=302)


# --- DÉTAIL ---
@router.get("/{id_type}")
def admin_typesdocuments_detail(id_type: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    t = db.query(TypeDocument).filter(TypeDocument.id_type == id_type).first()
    if not t:
        raise HTTPException(404, "Type de document non trouvé")

    return templates.TemplateResponse(
        "admin/typesdocuments/detail.html",
        {"request": request, "t": t},
    )


# --- EDITION ---
@router.get("/{id_type}/edit")
def admin_typesdocuments_edit(id_type: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    t = db.query(TypeDocument).filter(TypeDocument.id_type == id_type).first()
    if not t:
        raise HTTPException(404, "Type de document non trouvé")

    return templates.TemplateResponse(
        "admin/typesdocuments/form.html",
        {"request": request, "action": "Modifier", "type_document": t},
    )


@router.post("/{id_type}/edit")
def admin_typesdocuments_update(
    id_type: int,
    request: Request,
    libelle: str = Form(...),
    description: str = Form(...),
    db: Session = Depends(get_db),
):
    t = db.query(TypeDocument).filter(TypeDocument.id_type == id_type).first()
    if not t:
        raise HTTPException(404, "Type de document non trouvé")

    t.libelle = libelle
    t.description = description

    db.commit()

    return RedirectResponse(f"/admin/typesdocuments/{id_type}", status_code=302)


# --- SUPPRESSION ---
@router.get("/{id_type}/delete")
def admin_typesdocuments_delete(id_type: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    t = db.query(TypeDocument).filter(TypeDocument.id_type == id_type).first()
    if not t:
        raise HTTPException(404, "Type de document non trouvé")

    db.delete(t)
    db.commit()

    return RedirectResponse("/admin/typesdocuments", status_code=302)
