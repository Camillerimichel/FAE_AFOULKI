import io

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session
from openpyxl import Workbook

from app.database import get_db
from app.models.localite import Localite

router = APIRouter(prefix="/localites", tags=["Admin - Localites"])
templates = Jinja2Templates(directory="app/templates")


def check_session(request: Request) -> bool:
    if not request.state.user:
        return False
    return True


@router.get("/")
def admin_localites_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    localites = db.query(Localite).order_by(func.lower(Localite.nom)).all()

    return templates.TemplateResponse(
        "admin/localites/list.html",
        {"request": request, "localites": localites},
    )


@router.get("/export/excel")
def admin_localites_export_excel(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    localites = db.query(Localite).order_by(Localite.nom).all()

    wb = Workbook()
    ws = wb.active
    ws.title = "Localites"
    ws.append(["Nom", "Latitude", "Longitude", "Alias"])
    for loc in localites:
        ws.append([
            loc.nom,
            loc.latitude if loc.latitude is not None else "",
            loc.longitude if loc.longitude is not None else "",
            loc.aliases or "",
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    headers = {"Content-Disposition": "attachment; filename=localites.xlsx"}
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/new")
def admin_localite_new(request: Request):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    return templates.TemplateResponse(
        "admin/localites/form.html",
        {"request": request, "action": "Créer", "localite": None},
    )


@router.post("/new")
def admin_localite_create(
    request: Request,
    nom: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    aliases: str = Form(""),
    db: Session = Depends(get_db),
):
    existing = db.query(Localite).filter(Localite.nom == nom).first()
    if existing:
        raise HTTPException(400, "Localité déjà existante")

    localite = Localite(
        nom=nom.strip(),
        latitude=latitude,
        longitude=longitude,
        aliases=aliases.strip() if aliases else None,
    )
    db.add(localite)
    db.commit()

    return RedirectResponse("/admin/localites", status_code=302)


@router.get("/{id_localite}")
def admin_localite_detail(id_localite: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    localite = db.query(Localite).filter(Localite.id_localite == id_localite).first()
    if not localite:
        raise HTTPException(404, "Localité non trouvée")

    return templates.TemplateResponse(
        "admin/localites/detail.html",
        {"request": request, "localite": localite},
    )


@router.get("/{id_localite}/edit")
def admin_localite_edit(id_localite: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    localite = db.query(Localite).filter(Localite.id_localite == id_localite).first()
    if not localite:
        raise HTTPException(404, "Localité non trouvée")

    return templates.TemplateResponse(
        "admin/localites/form.html",
        {"request": request, "action": "Modifier", "localite": localite},
    )


@router.post("/{id_localite}/edit")
def admin_localite_update(
    id_localite: int,
    request: Request,
    nom: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    aliases: str = Form(""),
    db: Session = Depends(get_db),
):
    localite = db.query(Localite).filter(Localite.id_localite == id_localite).first()
    if not localite:
        raise HTTPException(404, "Localité non trouvée")

    existing = (
        db.query(Localite)
        .filter(Localite.nom == nom, Localite.id_localite != id_localite)
        .first()
    )
    if existing:
        raise HTTPException(400, "Localité déjà existante")

    localite.nom = nom.strip()
    localite.latitude = latitude
    localite.longitude = longitude
    localite.aliases = aliases.strip() if aliases else None
    db.commit()

    return RedirectResponse(f"/admin/localites/{id_localite}", status_code=302)


@router.get("/{id_localite}/delete")
def admin_localite_delete(id_localite: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    localite = db.query(Localite).filter(Localite.id_localite == id_localite).first()
    if not localite:
        raise HTTPException(404, "Localité non trouvée")

    db.delete(localite)
    db.commit()

    return RedirectResponse("/admin/localites", status_code=302)
