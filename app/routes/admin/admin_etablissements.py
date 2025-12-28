import io

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from openpyxl import Workbook

from app.database import get_db
from app.models.etablissement import ETABLISSEMENT_TYPES, Etablissement

router = APIRouter(prefix="/etablissements", tags=["Admin - Etablissements"])
templates = Jinja2Templates(directory="app/templates")


# --- Vérification session ---
def check_session(request: Request):
    if not request.state.user:
        return False
    return True


# --- LISTE ---
@router.get("/")
def admin_etablissements_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    etablissements = db.query(Etablissement).order_by(Etablissement.ville).all()

    return templates.TemplateResponse(
        "admin/etablissements/list.html",
        {"request": request, "etablissements": etablissements},
    )


@router.get("/export/excel")
def admin_etablissements_export_excel(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    etablissements = (
        db.query(Etablissement)
        .order_by(Etablissement.ville, Etablissement.nom)
        .all()
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Etablissements"
    ws.append(["ID", "Nom", "Ville", "Type", "Adresse"])
    for etab in etablissements:
        ws.append([
            etab.id_etablissement,
            etab.nom,
            etab.ville or "",
            etab.type or "",
            etab.adresse or "",
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    headers = {"Content-Disposition": "attachment; filename=etablissements.xlsx"}
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


# --- CREER ---
@router.get("/new")
def admin_etablissement_new(request: Request):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    return templates.TemplateResponse(
        "admin/etablissements/form.html",
        {
            "request": request,
            "action": "Créer",
            "etablissement": None,
            "etablissement_types": ETABLISSEMENT_TYPES,
        },
    )


@router.post("/new")
def admin_etablissement_create(
    request: Request,
    nom: str = Form(...),
    adresse: str = Form(...),
    ville: str = Form(...),
    type: str = Form(...),
    db: Session = Depends(get_db),
):
    if type not in ETABLISSEMENT_TYPES:
        raise HTTPException(400, "Type d'établissement invalide")

    etab = Etablissement(
        nom=nom,
        adresse=adresse,
        ville=ville,
        type=type,
    )
    db.add(etab)
    db.commit()

    return RedirectResponse("/admin/etablissements", status_code=302)


# --- DETAIL ---
@router.get("/{id_etablissement}")
def admin_etablissement_detail(id_etablissement: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    etab = (
        db.query(Etablissement)
        .filter(Etablissement.id_etablissement == id_etablissement)
        .first()
    )
    if not etab:
        raise HTTPException(404, "Établissement non trouvé")

    return templates.TemplateResponse(
        "admin/etablissements/detail.html",
        {"request": request, "etablissement": etab},
    )


# --- EDITER ---
@router.get("/{id_etablissement}/edit")
def admin_etablissement_edit(id_etablissement: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    etab = (
        db.query(Etablissement)
        .filter(Etablissement.id_etablissement == id_etablissement)
        .first()
    )
    if not etab:
        raise HTTPException(404, "Établissement non trouvé")

    return templates.TemplateResponse(
        "admin/etablissements/form.html",
        {
            "request": request,
            "action": "Modifier",
            "etablissement": etab,
            "etablissement_types": ETABLISSEMENT_TYPES,
        },
    )


@router.post("/{id_etablissement}/edit")
def admin_etablissement_update(
    id_etablissement: int,
    request: Request,
    nom: str = Form(...),
    adresse: str = Form(...),
    ville: str = Form(...),
    type: str = Form(...),
    db: Session = Depends(get_db),
):
    etab = (
        db.query(Etablissement)
        .filter(Etablissement.id_etablissement == id_etablissement)
        .first()
    )
    if not etab:
        raise HTTPException(404, "Établissement non trouvé")

    if type not in ETABLISSEMENT_TYPES:
        raise HTTPException(400, "Type d'établissement invalide")

    etab.nom = nom
    etab.adresse = adresse
    etab.ville = ville
    etab.type = type

    db.commit()

    return RedirectResponse(f"/admin/etablissements/{id_etablissement}", status_code=302)


# --- DELETE ---
@router.get("/{id_etablissement}/delete")
def admin_etablissement_delete(id_etablissement: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    etab = (
        db.query(Etablissement)
        .filter(Etablissement.id_etablissement == id_etablissement)
        .first()
    )
    if not etab:
        raise HTTPException(404, "Établissement non trouvé")

    db.delete(etab)
    db.commit()

    return RedirectResponse("/admin/etablissements", status_code=302)
