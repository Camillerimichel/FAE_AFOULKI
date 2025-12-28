import io
import os
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from openpyxl import Workbook

from app.database import BASE_DIR, get_db
from app.models.parrain import Parrain
from app.models.parrainage import Parrainage

router = APIRouter(prefix="/parrains", tags=["Admin - Parrains"])
templates = Jinja2Templates(directory="app/templates")
DOCUMENTS_DIR = BASE_DIR / "Documents" / "Parrains"


def parrain_dir_path(parrain_id: int) -> Path:
    return DOCUMENTS_DIR / str(parrain_id)


def ensure_parrain_dir(parrain_id: int) -> Path:
    file_dir = parrain_dir_path(parrain_id)
    file_dir.mkdir(parents=True, exist_ok=True)
    return file_dir


def save_photo_file(parrain_id: int, photo: UploadFile) -> str:
    file_dir = ensure_parrain_dir(parrain_id)
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


# --- Vérification session ---
def check_session(request: Request):
    if not request.state.user:
        return False
    return True


# --- LISTE ---
@router.get("/")
def admin_parrains_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    parrains = db.query(Parrain).order_by(Parrain.nom.asc(), Parrain.prenom.asc()).all()

    return templates.TemplateResponse(
        "admin/parrains/list.html",
        {"request": request, "parrains": parrains},
    )


@router.get("/export/excel")
def admin_parrains_export_excel(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    parrains = db.query(Parrain).order_by(Parrain.nom.asc(), Parrain.prenom.asc()).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Parrains"
    ws.append(["Nom", "Prénom", "Téléphone", "Email", "Adresse"])
    for p in parrains:
        ws.append([
            p.nom,
            p.prenom,
            p.telephone or "",
            p.email or "",
            p.adresse or "",
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    headers = {"Content-Disposition": "attachment; filename=parrains.xlsx"}
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
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
    telephone: str | None = Form(None),
    email: str | None = Form(None),
    adresse: str = Form(...),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    parrain = Parrain(
        nom=nom,
        prenom=prenom,
        telephone=normalize_optional(telephone),
        email=normalize_optional(email),
        adresse=adresse,
    )
    db.add(parrain)
    db.commit()
    db.refresh(parrain)

    ensure_parrain_dir(parrain.id_parrain)
    if photo and photo.filename:
        parrain.photo = save_photo_file(parrain.id_parrain, photo)
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
    telephone: str | None = Form(None),
    email: str | None = Form(None),
    adresse: str = Form(...),
    photo: UploadFile | None = File(None),
    remove_photo: str | None = Form(None),
    db: Session = Depends(get_db),
):
    parrain = db.query(Parrain).filter(Parrain.id_parrain == parrain_id).first()
    if not parrain:
        raise HTTPException(404, "Parrain non trouvé")

    parrain.nom = nom
    parrain.prenom = prenom
    parrain.telephone = normalize_optional(telephone)
    parrain.email = normalize_optional(email)
    parrain.adresse = adresse
    if photo and photo.filename:
        remove_photo_file(parrain.photo)
        parrain.photo = save_photo_file(parrain.id_parrain, photo)
    elif remove_photo:
        remove_photo_file(parrain.photo)
        parrain.photo = None

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

    remove_photo_file(parrain.photo)
    db.query(Parrainage).filter(Parrainage.id_parrain == parrain_id).delete(synchronize_session=False)
    db.delete(parrain)
    db.commit()

    parrain_dir = parrain_dir_path(parrain_id)
    if parrain_dir.exists():
        shutil.rmtree(parrain_dir)

    return RedirectResponse("/admin/parrains", status_code=302)
