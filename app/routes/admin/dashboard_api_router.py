from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import aliased

from app.database import SessionLocal
from app.models.filleule import Filleule
from app.models.etablissement import Etablissement
from app.models.parrainage import Parrainage
from app.models.scolarite import Scolarite

router = APIRouter(prefix="/admin/api", tags=["Admin API"])

def require_admin(request: Request):
    if not request.state.user:
        raise HTTPException(401, "Non authentifié")


@router.get("/filleuls-par-etab")
async def api_filleuls_par_etab(request: Request, etablissement_id: list[int] = None):
    require_admin(request)

    db = SessionLocal()

    query = (
        db.query(Etablissement.nom, func.count(Filleule.id_filleule))
        .join(Filleule, Filleule.etablissement_id == Etablissement.id_etablissement)
    )

    if etablissement_id:
       query = query.filter(Etablissement.id_etablissement.in_(etablissement_id))

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
            func.count(Parrainage.id_parrainage)
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
    latest_scolarite = (
        db.query(Scolarite.id_filleule, func.max(Scolarite.id_scolarite).label("max_id"))
        .group_by(Scolarite.id_filleule)
        .subquery()
    )
    ScolariteLatest = aliased(Scolarite)
    rows = (
        db.query(ScolariteLatest.niveau, func.count(ScolariteLatest.id_scolarite))
        .join(latest_scolarite, ScolariteLatest.id_scolarite == latest_scolarite.c.max_id)
        .group_by(ScolariteLatest.niveau)
        .all()
    )
    db.close()
    return JSONResponse({
        "labels": [r[0] for r in rows],
        "data": [r[1] for r in rows]
    })
