from fastapi import APIRouter, Query, Request, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import func
from openpyxl import Workbook

from app.authz import ADMIN_ROLES, has_any_role
from app.database import SessionLocal
from app.models.filleule import Filleule
from app.models.etablissement import Etablissement
from app.models.parrainage import Parrainage

router = APIRouter(prefix="/admin/export", tags=["Export Excel"])


def require_admin(request: Request):
    if not request.state.user:
        raise HTTPException(401, "Non authentifié")
    if not has_any_role(request, ADMIN_ROLES):
        raise HTTPException(403, "Accès refusé")


@router.get("/excel")
def export_excel(
    request: Request,
    etablissement_id: list[int] = Query(None),
    annee: int = None
):
    require_admin(request)

    db = SessionLocal()

    # Base query
    query = db.query(
        Filleule.nom,
        Filleule.prenom,
        Etablissement.nom.label("etablissement"),
        Filleule.niveau_scolaire
    ).join(Etablissement, Etablissement.id == Filleule.etablissement_id)

    # Filtre établissements (multi-sélection)
    if etablissement_id:
        query = query.filter(Filleule.etablissement_id.in_(etablissement_id))

    # Filtre année
    if annee:
        query = query.join(Parrainage, Parrainage.filleule_id == Filleule.id)
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
