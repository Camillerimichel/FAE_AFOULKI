from datetime import date
import io
import os
import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from openpyxl import Workbook

from app.database import BASE_DIR, get_db
from app.models.correspondant import Correspondant
from app.models.document import Document
from app.models.etablissement import Etablissement
from app.models.filleule import Filleule
from app.models.parrainage import Parrainage
from app.models.scolarite import Scolarite
from app.models.suivisocial import SuiviSocial
from app.models.localite import Localite
from app.services.localites_service import build_localites_map, resolve_localite_name

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


def normalize_optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise HTTPException(400, "Valeur invalide")


def get_extra_villes(db: Session, localites: list[Localite]) -> list[str]:
    localite_names = {localite.nom for localite in localites}
    rows = (
        db.query(Filleule.ville)
        .filter(Filleule.ville.isnot(None))
        .filter(func.trim(Filleule.ville) != "")
        .filter(func.lower(func.trim(Filleule.ville)) != "none")
        .distinct()
        .order_by(Filleule.ville)
        .all()
    )
    extra = []
    for row in rows:
        value = row[0]
        if value and value not in localite_names:
            extra.append(value)
    return extra


# --- MIDDLEWARE DE SECURITE ---
def check_session(request: Request):
    if not request.state.user:
        return None
    return request.state.user.id


# --- PAGE LISTE ---
@router.get("/")
def admin_filleules_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    filleules = db.query(Filleule).options(joinedload(Filleule.correspondant)).all()

    return templates.TemplateResponse(
        "admin/filleules/list.html",
        {
            "request": request,
            "filleules": filleules,
        },
    )


@router.get("/export/excel")
def admin_filleules_export_excel(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    filleules = (
        db.query(Filleule)
        .options(joinedload(Filleule.correspondant))
        .order_by(Filleule.nom.asc(), Filleule.prenom.asc())
        .all()
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Filleules"
    ws.append(["ID", "Nom", "Prénom", "WhatsApp", "Entrée au FAE", "ID Référent", "Référent"])
    for f in filleules:
        referent = ""
        if f.correspondant:
            referent = f"{f.correspondant.prenom} {f.correspondant.nom}"
        ws.append([
            f.id_filleule,
            f.nom,
            f.prenom,
            f.whatsapp or "",
            f.annee_rentree or "",
            f.id_correspondant or "",
            referent,
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    headers = {"Content-Disposition": "attachment; filename=filleules.xlsx"}
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


# --- PAGE CREER ---
@router.get("/new")
def admin_filleule_new(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    etablissements = db.query(Etablissement).order_by(Etablissement.nom).all()
    correspondants = db.query(Correspondant).order_by(Correspondant.nom, Correspondant.prenom).all()
    localites = db.query(Localite).order_by(Localite.nom).all()
    extra_villes = get_extra_villes(db, localites)

    return templates.TemplateResponse(
        "admin/filleules/form.html",
        {
            "request": request,
            "action": "Créer",
            "filleule": None,
            "etablissements": etablissements,
            "correspondants": correspondants,
            "localites": localites,
            "extra_villes": extra_villes,
            "selected_ville": None,
        },
    )


@router.post("/new")
def admin_filleule_create(
    request: Request,
    nom: str = Form(...),
    prenom: str = Form(...),
    date_naissance: str = Form(...),
    village: str | None = Form(None),
    ville: str | None = Form(None),
    email: str | None = Form(None),
    telephone: str | None = Form(None),
    whatsapp: str | None = Form(None),
    etat_civil: str | None = Form(None),
    profession_pere: str | None = Form(None),
    profession_mere: str | None = Form(None),
    couverture_sante: str | None = Form(None),
    annee_rentree: str | None = Form(None),
    etablissement_id: int | None = Form(None),
    id_correspondant: str | None = Form(None),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    localites = db.query(Localite).order_by(Localite.nom).all()
    localites_map = build_localites_map(localites)
    resolved_ville = resolve_localite_name(ville, localites_map)
    photo_path = None
    obj = Filleule(
        nom=nom,
        prenom=prenom,
        date_naissance=date.fromisoformat(date_naissance) if date_naissance else None,
        village=normalize_optional(village),
        ville=normalize_optional(resolved_ville or ville),
        email=normalize_optional(email),
        telephone=normalize_optional(telephone),
        whatsapp=normalize_optional(whatsapp),
        etat_civil=normalize_optional(etat_civil),
        profession_pere=normalize_optional(profession_pere),
        profession_mere=normalize_optional(profession_mere),
        couverture_sante=normalize_optional(couverture_sante),
        annee_rentree=normalize_optional(annee_rentree),
        etablissement_id=etablissement_id,
        id_correspondant=normalize_optional_int(id_correspondant),
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

    previous_obj = (
        db.query(Filleule)
        .filter(Filleule.id_filleule < filleule_id)
        .order_by(Filleule.id_filleule.desc())
        .first()
    )
    next_obj = (
        db.query(Filleule)
        .filter(Filleule.id_filleule > filleule_id)
        .order_by(Filleule.id_filleule.asc())
        .first()
    )

    return templates.TemplateResponse(
        "admin/filleules/detail.html",
        {
            "request": request,
            "filleule": obj,
            "previous_filleule_id": previous_obj.id_filleule if previous_obj else None,
            "next_filleule_id": next_obj.id_filleule if next_obj else None,
        },
    )


# --- PAGE EDITER ---
@router.get("/{filleule_id}/edit")
def admin_filleule_edit(filleule_id: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    obj = db.query(Filleule).filter(Filleule.id_filleule == filleule_id).first()
    if not obj:
        raise HTTPException(404, "Filleule non trouvée")

    previous_obj = (
        db.query(Filleule)
        .filter(Filleule.id_filleule < filleule_id)
        .order_by(Filleule.id_filleule.desc())
        .first()
    )
    next_obj = (
        db.query(Filleule)
        .filter(Filleule.id_filleule > filleule_id)
        .order_by(Filleule.id_filleule.asc())
        .first()
    )

    etablissements = db.query(Etablissement).order_by(Etablissement.nom).all()
    correspondants = db.query(Correspondant).order_by(Correspondant.nom, Correspondant.prenom).all()
    localites = db.query(Localite).order_by(Localite.nom).all()
    localites_map = build_localites_map(localites)
    selected_ville = resolve_localite_name(obj.ville, localites_map) or obj.ville
    extra_villes = get_extra_villes(db, localites)

    return templates.TemplateResponse(
        "admin/filleules/form.html",
        {
            "request": request,
            "action": "Modifier",
            "filleule": obj,
            "etablissements": etablissements,
            "correspondants": correspondants,
            "localites": localites,
            "extra_villes": extra_villes,
            "selected_ville": selected_ville,
            "previous_filleule_id": previous_obj.id_filleule if previous_obj else None,
            "next_filleule_id": next_obj.id_filleule if next_obj else None,
        },
    )


@router.post("/{filleule_id}/edit")
def admin_filleule_update(
    filleule_id: int,
    request: Request,
    nom: str = Form(...),
    prenom: str = Form(...),
    date_naissance: str = Form(...),
    village: str | None = Form(None),
    ville: str | None = Form(None),
    email: str | None = Form(None),
    telephone: str | None = Form(None),
    whatsapp: str | None = Form(None),
    etat_civil: str | None = Form(None),
    profession_pere: str | None = Form(None),
    profession_mere: str | None = Form(None),
    couverture_sante: str | None = Form(None),
    annee_rentree: str | None = Form(None),
    etablissement_id: int | None = Form(None),
    id_correspondant: str | None = Form(None),
    photo: UploadFile | None = File(None),
    remove_photo: str | None = Form(None),
    db: Session = Depends(get_db),
):
    obj = db.query(Filleule).filter(Filleule.id_filleule == filleule_id).first()
    if not obj:
        raise HTTPException(404, "Filleule non trouvée")

    localites = db.query(Localite).order_by(Localite.nom).all()
    localites_map = build_localites_map(localites)
    resolved_ville = resolve_localite_name(ville, localites_map)

    obj.nom = nom
    obj.prenom = prenom
    obj.date_naissance = date.fromisoformat(date_naissance) if date_naissance else None
    if village is not None:
        obj.village = normalize_optional(village)
    obj.ville = normalize_optional(resolved_ville or ville)
    obj.email = normalize_optional(email)
    obj.telephone = normalize_optional(telephone)
    obj.whatsapp = normalize_optional(whatsapp)
    obj.etat_civil = normalize_optional(etat_civil)
    obj.profession_pere = normalize_optional(profession_pere)
    obj.profession_mere = normalize_optional(profession_mere)
    obj.couverture_sante = normalize_optional(couverture_sante)
    obj.annee_rentree = normalize_optional(annee_rentree)
    if etablissement_id is not None:
        obj.etablissement_id = etablissement_id
    obj.id_correspondant = normalize_optional_int(id_correspondant)
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
    db.query(Scolarite).filter(Scolarite.id_filleule == filleule_id).delete(synchronize_session=False)
    db.query(SuiviSocial).filter(SuiviSocial.id_filleule == filleule_id).delete(synchronize_session=False)
    db.query(Parrainage).filter(Parrainage.id_filleule == filleule_id).delete(synchronize_session=False)

    db.delete(obj)
    db.commit()

    filleule_dir = filleule_dir_path(filleule_id)
    if filleule_dir.exists():
        shutil.rmtree(filleule_dir)

    return RedirectResponse("/admin/filleules", status_code=302)
