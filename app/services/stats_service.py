from sqlalchemy.orm import Session
from app.database import SessionLocal

from app.models.filleule import Filleule
from app.models.parrain import Parrain
from app.models.parrainage import Parrainage
from app.models.document import Document

async def get_dashboard_stats():
    db: Session = SessionLocal()

    stats = {
        "filleules": db.query(Filleule).count(),
        "parrains": db.query(Parrain).count(),
        "parrainages": db.query(Parrainage).count(),
        "documents": db.query(Document).count(),
    }

    db.close()
    return stats
from sqlalchemy import func
from app.models.etablissement import Etablissement

async def get_chart_data():
    db = SessionLocal()

    # 1. Nombre de filleuls par établissement
    filleuls_par_etab = (
        db.query(Etablissement.nom, func.count(Filleule.id))
        .join(Filleule, Filleule.etablissement_id == Etablissement.id)
        .group_by(Etablissement.nom)
        .all()
    )

    # 2. Nombre de parrainages par année
    parrainages_par_annee = (
        db.query(func.extract('year', Parrainage.date_debut).label("annee"),
                 func.count(Parrainage.id))
        .group_by("annee")
        .order_by("annee")
        .all()
    )

    # Liste des établissements
    etablissements = db.query(Etablissement.nom, Etablissement.id).all()

    # Liste des années présentes dans les parrainages
    annees = db.query(func.extract('year', Parrainage.date_debut)).distinct().all()
    annees = [int(a[0]) for a in annees]

    # 3. Répartition des filleuls par niveau scolaire
    niveaux = (
        db.query(Filleule.niveau_scolaire, func.count(Filleule.id))
        .group_by(Filleule.niveau_scolaire)
        .all()
    )

    niveaux_labels = [n[0] for n in niveaux]
    niveaux_data = [n[1] for n in niveaux]


    db.close()

    return {
        "filleuls_par_etab": filleuls_par_etab,
        "parrainages_par_annee": parrainages_par_annee,
        "etablissements": etablissements,
        "annees": annees,
        "niveaux_labels": niveaux_labels,
        "niveaux_data": niveaux_data,
    }
