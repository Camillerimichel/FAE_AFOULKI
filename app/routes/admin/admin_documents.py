import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import BASE_DIR, get_db
from app.models.document import Document
from app.models.annee_scolaire import AnneeScolaire
from app.models.filleule import Filleule
from app.models.typedocument import TypeDocument

DOCUMENTS_DIR = BASE_DIR / "Documents" / "Filleules"

router = APIRouter(prefix="/documents", tags=["Admin - Documents"])
templates = Jinja2Templates(directory="app/templates")


def resolve_document_path(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


# --- Vérification session ---
def check_session(request: Request):
    if not request.state.user:
        return False
    return True


# --- LISTE ---
@router.get("/")
def admin_documents_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    docs = db.query(Document).all()

    return templates.TemplateResponse(
        "admin/documents/list.html",
        {"request": request, "documents": docs},
    )


# --- NOUVEAU ---
@router.get("/new")
def admin_documents_new(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    filleules = db.query(Filleule).all()
    types = db.query(TypeDocument).all()
    annees = db.query(AnneeScolaire).order_by(AnneeScolaire.periode).all()

    return templates.TemplateResponse(
        "admin/documents/form.html",
        {"request": request, "action": "Créer", "document": None,
         "filleules": filleules, "types": types, "annees": annees},
    )


@router.post("/new")
def admin_documents_create(
    request: Request,
    id_filleule: int = Form(...),
    id_type: int = Form(...),
    id_annee_scolaire: int = Form(...),
    titre: str = Form(...),
    fichier: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    # On crée un nom unique dans le dossier de la filleule
    file_dir = DOCUMENTS_DIR / str(id_filleule)
    file_dir.mkdir(parents=True, exist_ok=True)
    original_name = Path(fichier.filename or "document").name
    filename = f"{uuid4().hex}_{original_name}"
    save_path = file_dir / filename

    with save_path.open("wb") as buffer:
        buffer.write(fichier.file.read())

    relative_path = save_path.relative_to(BASE_DIR).as_posix()
    doc = Document(
        id_filleule=id_filleule,
        id_type=id_type,
        id_annee_scolaire=id_annee_scolaire,
        titre=titre,
        chemin_fichier=relative_path,
    )

    db.add(doc)
    db.commit()

    return RedirectResponse("/admin/documents", status_code=302)


# --- DÉTAIL ---
@router.get("/{id_document}")
def admin_documents_detail(id_document: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    d = db.query(Document).filter(Document.id_document == id_document).first()
    if not d:
        raise HTTPException(404, "Document non trouvé")

    return templates.TemplateResponse(
        "admin/documents/detail.html",
        {"request": request, "d": d},
    )


# --- EDIT ---
@router.get("/{id_document}/edit")
def admin_documents_edit(id_document: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    d = db.query(Document).filter(Document.id_document == id_document).first()
    if not d:
        raise HTTPException(404, "Document non trouvé")

    filleules = db.query(Filleule).all()
    types = db.query(TypeDocument).all()
    annees = db.query(AnneeScolaire).order_by(AnneeScolaire.periode).all()

    return templates.TemplateResponse(
        "admin/documents/form.html",
        {"request": request, "action": "Modifier", "document": d,
         "filleules": filleules, "types": types, "annees": annees},
    )


@router.post("/{id_document}/edit")
def admin_documents_update(
    id_document: int,
    request: Request,
    id_filleule: int = Form(...),
    id_type: int = Form(...),
    id_annee_scolaire: int = Form(...),
    titre: str = Form(...),
    db: Session = Depends(get_db),
):
    d = db.query(Document).filter(Document.id_document == id_document).first()
    if not d:
        raise HTTPException(404, "Document non trouvé")

    d.id_filleule = id_filleule
    d.id_type = id_type
    d.id_annee_scolaire = id_annee_scolaire
    d.titre = titre

    db.commit()

    return RedirectResponse(f"/admin/documents/{id_document}", status_code=302)


# --- DELETE ---
@router.get("/{id_document}/delete")
def admin_documents_delete(id_document: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    d = db.query(Document).filter(Document.id_document == id_document).first()
    if not d:
        raise HTTPException(404, "Document non trouvé")

    # Supprimer fichier si existant
    file_path = resolve_document_path(d.chemin_fichier)
    if file_path and file_path.exists():
        os.remove(file_path)

    db.delete(d)
    db.commit()

    return RedirectResponse("/admin/documents", status_code=302)
