from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import aliased
from openpyxl import Workbook

from app.database import SessionLocal
from app.models.filleule import Filleule
from app.models.etablissement import Etablissement
from app.models.parrainage import Parrainage
from app.models.scolarite import Scolarite

router = APIRouter(prefix="/admin/export", tags=["Export Excel"])


def require_admin(request: Request):
    if not request.state.user:
        raise HTTPException(401, "Non authentifié")


@router.get("/excel")
def export_excel(
    request: Request,
    etablissement_id: list[int] = Query(None),
    annee: int = None
):
    require_admin(request)

    db = SessionLocal()

    # Base query
    latest_scolarite = (
        db.query(Scolarite.id_filleule, func.max(Scolarite.id_scolarite).label("max_id"))
        .group_by(Scolarite.id_filleule)
        .subquery()
    )
    ScolariteLatest = aliased(Scolarite)

    query = db.query(
        Filleule.nom,
        Filleule.prenom,
        Etablissement.nom.label("etablissement"),
        ScolariteLatest.niveau.label("niveau_scolaire"),
    ).join(
        Etablissement,
        Etablissement.id_etablissement == Filleule.etablissement_id,
    ).outerjoin(
        latest_scolarite,
        latest_scolarite.c.id_filleule == Filleule.id_filleule,
    ).outerjoin(
        ScolariteLatest,
        ScolariteLatest.id_scolarite == latest_scolarite.c.max_id,
    )

    # Filtre établissements (multi-sélection)
    if etablissement_id:
        query = query.filter(Filleule.etablissement_id.in_(etablissement_id))

    # Filtre année
    if annee:
        query = query.join(Parrainage, Parrainage.id_filleule == Filleule.id_filleule)
        query = query.filter(func.extract('year', Parrainage.date_debut) == annee)

    rows = query.all()
    db.close()

    # Génération Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Données filtrées"

    # En-têtes
    ws.append(["Nom", "Prénom", "Établissement", "Niveau scolaire"])

    # Lignes du tableau
    for r in rows:
        ws.append(list(r))

    file_path = "/tmp/export.xlsx"
    wb.save(file_path)

    return FileResponse(file_path, filename="export.xlsx")
