from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import func

from app.authz import ADMIN_ROLES, has_any_role
from app.database import SessionLocal
from app.models.filleule import Filleule
from app.models.etablissement import Etablissement
from app.models.parrainage import Parrainage

router = APIRouter(prefix="/admin/api", tags=["Admin API"])

def require_admin(request: Request):
    if not request.state.user:
        raise HTTPException(401, "Non authentifié")
    if not has_any_role(request, ADMIN_ROLES):
        raise HTTPException(403, "Accès refusé")


@router.get("/filleuls-par-etab")
async def api_filleuls_par_etab(request: Request, etablissement_id: list[int] = None):
    require_admin(request)

    db = SessionLocal()

    query = (
        db.query(Etablissement.nom, func.count(Filleule.id))
        .join(Filleule, Filleule.etablissement_id == Etablissement.id)
    )

    if etablissement_id:
       query = query.filter(Etablissement.id.in_(etablissement_id))

    rows = query.group_by(Etablissement.nom).all()
    db.close()

    labels = [r[0] for r in rows]
    data = [r[1] for r in rows]

    return JSONResponse({"labels": labels, "data": data})


@router.get("/parrainages-par-annee")
async def api_parrainages_par_annee(request: Request, annee: int = None):
    require_admin(request)
    db = SessionLocal()

    query = (
        db.query(
            func.extract('year', Parrainage.date_debut).label("annee"),
            func.count(Parrainage.id)
        )
    )

    if annee:
        query = query.filter(func.extract('year', Parrainage.date_debut) == annee)

    rows = query.group_by("annee").order_by("annee").all()
    db.close()

    labels = [int(r[0]) for r in rows]
    data = [r[1] for r in rows]

    return JSONResponse({"labels": labels, "data": data})

@router.get("/niveau-scolaire")
async def api_niveau_scolaire(request: Request):
    require_admin(request)
    db = SessionLocal()
    rows = (
        db.query(Filleule.niveau_scolaire, func.count(Filleule.id))
        .group_by(Filleule.niveau_scolaire)
        .all()
    )
    db.close()
    return JSONResponse({
        "labels": [r[0] for r in rows],
        "data": [r[1] for r in rows]
    })
