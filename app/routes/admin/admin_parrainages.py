import io

from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from datetime import date
from openpyxl import Workbook

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
    return True


def normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def parse_optional_int(value: str | None) -> int | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    return int(value)


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


@router.get("/export/excel")
def admin_parrainages_export_excel(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    parrainages = (
        db.query(Parrainage)
        .options(joinedload(Parrainage.parrain), joinedload(Parrainage.filleule))
        .order_by(Parrainage.id_parrainage.asc())
        .all()
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Parrainages"
    ws.append([
        "Parrain nom",
        "Parrain prénom",
        "Filleule nom",
        "Filleule prénom",
        "Début",
        "Fin",
        "Statut",
    ])
    for p in parrainages:
        parrain = p.parrain
        filleule = p.filleule
        ws.append([
            parrain.nom if parrain else "",
            parrain.prenom if parrain else "",
            filleule.nom if filleule else "",
            filleule.prenom if filleule else "",
            p.date_debut.isoformat() if p.date_debut else "",
            p.date_fin.isoformat() if p.date_fin else "",
            p.statut or "",
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    headers = {"Content-Disposition": "attachment; filename=parrainages.xlsx"}
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


# --- CREER ---
@router.get("/new")
def admin_parrainage_new(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    parrains = db.query(Parrain).order_by(Parrain.nom, Parrain.prenom).all()
    filleules = db.query(Filleule).order_by(Filleule.nom, Filleule.prenom).all()

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
    date_debut: str | None = Form(None),
    date_fin: str | None = Form(None),
    statut: str | None = Form(None),
    bourse_centre: str | None = Form(None),
    bourse_rw: str | None = Form(None),
    db: Session = Depends(get_db),
):
    obj = Parrainage(
        id_parrain=id_parrain,
        id_filleule=id_filleule,
        date_debut=date.fromisoformat(date_debut) if date_debut else None,
        date_fin=date.fromisoformat(date_fin) if date_fin else None,
        statut=normalize_optional_text(statut),
        bourse_centre=parse_optional_int(bourse_centre),
        bourse_rw=parse_optional_int(bourse_rw),
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

    parrains = db.query(Parrain).order_by(Parrain.nom, Parrain.prenom).all()
    filleules = db.query(Filleule).order_by(Filleule.nom, Filleule.prenom).all()

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
    date_debut: str | None = Form(None),
    date_fin: str | None = Form(None),
    statut: str | None = Form(None),
    bourse_centre: str | None = Form(None),
    bourse_rw: str | None = Form(None),
    db: Session = Depends(get_db),
):

    obj = db.query(Parrainage).filter(Parrainage.id_parrainage == id_parrainage).first()
    if not obj:
        raise HTTPException(404, "Parrainage non trouvé")

    obj.id_parrain = id_parrain
    obj.id_filleule = id_filleule
    obj.date_debut = date.fromisoformat(date_debut) if date_debut else None
    obj.date_fin = date.fromisoformat(date_fin) if date_fin else None
    obj.statut = normalize_optional_text(statut)
    obj.bourse_centre = parse_optional_int(bourse_centre)
    obj.bourse_rw = parse_optional_int(bourse_rw)

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
