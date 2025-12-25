from datetime import date
import os
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.authz import ADMIN_ROLES, has_any_role
from app.database import BASE_DIR, get_db
from app.models.correspondant import Correspondant
from app.models.document import Document
from app.models.etablissement import Etablissement
from app.models.filleule import Filleule
from app.models.parrainage import Parrainage
from app.models.scolarite import Scolarite
from app.models.suivisocial import SuiviSocial

router = APIRouter(prefix="/filleules", tags=["Admin - Filleules"])
templates = Jinja2Templates(directory="app/templates")
DOCUMENTS_DIR = BASE_DIR / "Documents" / "Filleules"


def filleule_dir_path(filleule_id: int) -> Path:
    return DOCUMENTS_DIR / str(filleule_id)


def ensure_filleule_dir(filleule_id: int) -> Path:
    file_dir = filleule_dir_path(filleule_id)
    file_dir.mkdir(parents=True, exist_ok=True)
    return file_dir


def save_photo_file(filleule_id: int, photo: UploadFile) -> str:
    file_dir = ensure_filleule_dir(filleule_id)
    ext = Path(photo.filename or "").suffix
    filename = f"photo_{uuid4().hex}{ext}"
    file_path = file_dir / filename
    with file_path.open("wb") as buffer:
        buffer.write(photo.file.read())
    return file_path.relative_to(BASE_DIR).as_posix()


def remove_photo_file(photo_path: str | None) -> None:
    if not photo_path:
        return
    path = Path(photo_path)
    if not path.is_absolute():
        path = BASE_DIR / path
    if path.exists():
        os.remove(path)


def normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


# --- MIDDLEWARE DE SECURITE ---
def check_session(request: Request):
    if not request.state.user:
        return None
    if not has_any_role(request, ADMIN_ROLES):
        raise HTTPException(403, "Accès refusé")
    return request.state.user.id


# --- PAGE LISTE ---
@router.get("/")
def admin_filleules_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    filleules = db.query(Filleule).all()

    return templates.TemplateResponse(
        "admin/filleules/list.html",
        {"request": request, "filleules": filleules},
    )


# --- PAGE CREER ---
@router.get("/new")
def admin_filleule_new(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    etablissements = db.query(Etablissement).all()

    return templates.TemplateResponse(
        "admin/filleules/form.html",
        {
            "request": request,
            "action": "Créer",
            "filleule": None,
            "etablissements": etablissements,
        },
    )


@router.post("/new")
def admin_filleule_create(
    request: Request,
    nom: str = Form(...),
    prenom: str = Form(...),
    date_naissance: str = Form(...),
    village: str = Form(...),
    ville: str | None = Form(None),
    email: str | None = Form(None),
    telephone: str | None = Form(None),
    whatsapp: str | None = Form(None),
    etat_civil: str | None = Form(None),
    annee_rentree: str | None = Form(None),
    etablissement_id: int = Form(...),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    photo_path = None
    obj = Filleule(
        nom=nom,
        prenom=prenom,
        date_naissance=date.fromisoformat(date_naissance) if date_naissance else None,
        village=village,
        ville=normalize_optional(ville),
        email=normalize_optional(email),
        telephone=normalize_optional(telephone),
        whatsapp=normalize_optional(whatsapp),
        etat_civil=normalize_optional(etat_civil),
        annee_rentree=normalize_optional(annee_rentree),
        etablissement_id=etablissement_id,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)

    ensure_filleule_dir(obj.id_filleule)

    if photo and photo.filename:
        photo_path = save_photo_file(obj.id_filleule, photo)
        obj.photo = photo_path
        db.commit()

    return RedirectResponse("/admin/filleules", status_code=302)


# --- PAGE DETAIL ---
@router.get("/{filleule_id}")
def admin_filleule_detail(filleule_id: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    obj = db.query(Filleule).filter(Filleule.id_filleule == filleule_id).first()
    if not obj:
        raise HTTPException(404, "Filleule non trouvée")

    return templates.TemplateResponse(
        "admin/filleules/detail.html",
        {"request": request, "filleule": obj},
    )


# --- PAGE EDITER ---
@router.get("/{filleule_id}/edit")
def admin_filleule_edit(filleule_id: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    obj = db.query(Filleule).filter(Filleule.id_filleule == filleule_id).first()
    if not obj:
        raise HTTPException(404, "Filleule non trouvée")

    etablissements = db.query(Etablissement).all()

    return templates.TemplateResponse(
        "admin/filleules/form.html",
        {
            "request": request,
            "action": "Modifier",
            "filleule": obj,
            "etablissements": etablissements,
        },
    )


@router.post("/{filleule_id}/edit")
def admin_filleule_update(
    filleule_id: int,
    request: Request,
    nom: str = Form(...),
    prenom: str = Form(...),
    date_naissance: str = Form(...),
    village: str = Form(...),
    ville: str | None = Form(None),
    email: str | None = Form(None),
    telephone: str | None = Form(None),
    whatsapp: str | None = Form(None),
    etat_civil: str | None = Form(None),
    annee_rentree: str | None = Form(None),
    etablissement_id: int = Form(...),
    photo: UploadFile | None = File(None),
    remove_photo: str | None = Form(None),
    db: Session = Depends(get_db),
):
    obj = db.query(Filleule).filter(Filleule.id_filleule == filleule_id).first()
    if not obj:
        raise HTTPException(404, "Filleule non trouvée")

    obj.nom = nom
    obj.prenom = prenom
    obj.date_naissance = date.fromisoformat(date_naissance) if date_naissance else None
    obj.village = village
    obj.ville = normalize_optional(ville)
    obj.email = normalize_optional(email)
    obj.telephone = normalize_optional(telephone)
    obj.whatsapp = normalize_optional(whatsapp)
    obj.etat_civil = normalize_optional(etat_civil)
    obj.annee_rentree = normalize_optional(annee_rentree)
    obj.etablissement_id = etablissement_id
    if photo and photo.filename:
        remove_photo_file(obj.photo)
        obj.photo = save_photo_file(obj.id_filleule, photo)
    elif remove_photo:
        remove_photo_file(obj.photo)
        obj.photo = None

    db.commit()

    return RedirectResponse(f"/admin/filleules/{filleule_id}", status_code=302)


# --- SUPPRESSION ---
@router.get("/{filleule_id}/delete")
def admin_filleule_delete(filleule_id: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    obj = db.query(Filleule).filter(Filleule.id_filleule == filleule_id).first()
    if not obj:
        raise HTTPException(404, "Filleule non trouvée")

    remove_photo_file(obj.photo)

    docs = db.query(Document).filter(Document.id_filleule == filleule_id).all()
    for doc in docs:
        remove_photo_file(doc.chemin_fichier)

    db.query(Document).filter(Document.id_filleule == filleule_id).delete(synchronize_session=False)
    db.query(Correspondant).filter(Correspondant.id_filleule == filleule_id).delete(synchronize_session=False)
    db.query(Scolarite).filter(Scolarite.id_filleule == filleule_id).delete(synchronize_session=False)
    db.query(SuiviSocial).filter(SuiviSocial.id_filleule == filleule_id).delete(synchronize_session=False)
    db.query(Parrainage).filter(Parrainage.id_filleule == filleule_id).delete(synchronize_session=False)

    db.delete(obj)
    db.commit()

    filleule_dir = filleule_dir_path(filleule_id)
    if filleule_dir.exists():
        shutil.rmtree(filleule_dir)

    return RedirectResponse("/admin/filleules", status_code=302)
