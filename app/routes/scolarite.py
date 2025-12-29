import io
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import joinedload
from openpyxl import Workbook

from app.database import get_db
from app.models.scolarite import Scolarite
from app.models.annee_scolaire import AnneeScolaire
from app.models.correspondant import Correspondant
from app.schemas.scolarite import ScolariteCreate, ScolariteResponse

router = APIRouter(prefix="/scolarite", tags=["Scolarité"])

# Templates
templates = Jinja2Templates(directory="app/templates")


def check_session(request: Request) -> bool:
    if not request.state.user:
        return False
    return True


def resolve_correspondant_label(
    value: Optional[str],
    correspondants: list[Correspondant],
) -> Optional[str]:
    if not value:
        return None
    value_str = str(value).strip()
    if value_str.isdigit():
        for correspondant in correspondants:
            if correspondant.id_correspondant == int(value_str):
                return f"{correspondant.prenom} {correspondant.nom}".strip()
        return value_str
    return value_str


@router.get("/", response_model=list[ScolariteResponse])
def get_all_scolarite(db: Session = Depends(get_db)):
    return db.query(Scolarite).all()


# ----------------------------------------------------------------------
#   ROUTE HTML POUR ÉVITER L'ERREUR /scolarite/html
# ----------------------------------------------------------------------
@router.get("/html")
def scolarite_html(
    request: Request,
    annee: str | None = None,
    db: Session = Depends(get_db),
):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    query = db.query(Scolarite).options(
        joinedload(Scolarite.filleule),
        joinedload(Scolarite.etablissement),
        joinedload(Scolarite.annee_scolaire_ref),
    )
    annee_filter = None
    if annee:
        annee_value = annee.strip()
        if annee_value.isdigit():
            annee_id = int(annee_value)
            query = query.filter(Scolarite.id_annee_scolaire == annee_id)
            row = (
                db.query(AnneeScolaire.periode)
                .filter(AnneeScolaire.id_annee_scolaire == annee_id)
                .first()
            )
            if row:
                annee_filter = row[0]
        else:
            query = query.outerjoin(Scolarite.annee_scolaire_ref).filter(
                or_(
                    Scolarite.annee_scolaire == annee_value,
                    AnneeScolaire.periode == annee_value,
                )
            )
            annee_filter = annee_value

    liste = query.all()
    correspondants = (
        db.query(Correspondant)
        .order_by(Correspondant.prenom, Correspondant.nom)
        .all()
    )
    referent_labels = {
        s.id_scolarite: resolve_correspondant_label(s.referent_a, correspondants)
        for s in liste
    }
    return templates.TemplateResponse(
        "scolarite_html.html",
        {
            "request": request,
            "scolarites": liste,
            "referent_labels": referent_labels,
            "annee_filter": annee_filter,
        },
    )
# ----------------------------------------------------------------------


@router.get("/export/excel")
def scolarite_export_excel(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    scolarites = (
        db.query(Scolarite)
        .options(
            joinedload(Scolarite.filleule),
            joinedload(Scolarite.etablissement),
            joinedload(Scolarite.annee_scolaire_ref),
        )
        .order_by(Scolarite.id_scolarite.asc())
        .all()
    )
    correspondants = (
        db.query(Correspondant)
        .order_by(Correspondant.prenom, Correspondant.nom)
        .all()
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Scolarite"
    ws.append(["Filleule", "Référent A", "Établissement", "Année scolaire", "Niveau"])
    for s in scolarites:
        filleule = ""
        if s.filleule:
            filleule = f"{s.filleule.prenom} {s.filleule.nom}".strip()
        referent = resolve_correspondant_label(s.referent_a, correspondants) or ""
        etablissement = s.etablissement.nom if s.etablissement else ""
        annee = s.annee_scolaire_ref.periode if s.annee_scolaire_ref else s.annee_scolaire
        ws.append([
            filleule,
            referent,
            etablissement,
            annee or "",
            s.niveau or "",
        ])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    headers = {"Content-Disposition": "attachment; filename=scolarite.xlsx"}
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )


@router.get("/{scolarite_id}", response_model=ScolariteResponse)
def get_scolarite(scolarite_id: int, db: Session = Depends(get_db)):
    record = db.query(Scolarite).filter(Scolarite.id_scolarite == scolarite_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Enregistrement de scolarité introuvable")
    return record


@router.post("/", response_model=ScolariteResponse)
def create_scolarite(data: ScolariteCreate, db: Session = Depends(get_db)):
    payload = data.dict()
    annee_id = payload.get("id_annee_scolaire")
    if annee_id and not payload.get("annee_scolaire"):
        annee = (
            db.query(AnneeScolaire)
            .filter(AnneeScolaire.id_annee_scolaire == annee_id)
            .first()
        )
        if not annee:
            raise HTTPException(status_code=400, detail="Année scolaire invalide")
        payload["annee_scolaire"] = annee.periode

    record = Scolarite(**payload)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{scolarite_id}", response_model=ScolariteResponse)
def update_scolarite(scolarite_id: int, data: ScolariteCreate, db: Session = Depends(get_db)):
    record = db.query(Scolarite).filter(Scolarite.id_scolarite == scolarite_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Enregistrement de scolarité introuvable")

    payload = data.dict()
    annee_id = payload.get("id_annee_scolaire")
    if annee_id and not payload.get("annee_scolaire"):
        annee = (
            db.query(AnneeScolaire)
            .filter(AnneeScolaire.id_annee_scolaire == annee_id)
            .first()
        )
        if not annee:
            raise HTTPException(status_code=400, detail="Année scolaire invalide")
        payload["annee_scolaire"] = annee.periode

    for key, value in payload.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{scolarite_id}")
def delete_scolarite(scolarite_id: int, db: Session = Depends(get_db)):
    record = db.query(Scolarite).filter(Scolarite.id_scolarite == scolarite_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Enregistrement de scolarité introuvable")

    db.delete(record)
    db.commit()
    return {"message": "Scolarité supprimée"}
