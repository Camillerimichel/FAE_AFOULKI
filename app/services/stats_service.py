import json
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.database import SessionLocal
from app.models.document import Document
from app.models.correspondant import Correspondant
from app.models.etablissement import Etablissement
from app.models.filleule import Filleule
from app.models.localite import Localite
from app.models.parrain import Parrain
from app.models.parrainage import Parrainage
from app.models.scolarite import Scolarite

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CITY_COORDS_PATH = DATA_DIR / "city_coords.json"
ESSAOUIRA_MAP_PATH = DATA_DIR / "essaouira_map.json"


def normalize_city_name(name: str) -> str:
    return " ".join(name.split()).strip().lower()


def load_city_coords() -> dict:
    if not CITY_COORDS_PATH.exists():
        return {}
    try:
        with CITY_COORDS_PATH.open("r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(data, dict):
        return data
    return {}


def get_essaouira_map() -> dict | None:
    if not ESSAOUIRA_MAP_PATH.exists():
        return None
    try:
        with ESSAOUIRA_MAP_PATH.open("r", encoding="utf-8") as file_obj:
            return json.load(file_obj)
    except (OSError, json.JSONDecodeError):
        return None


async def get_dashboard_stats():
    db: Session = SessionLocal()

    stats = {
        "filleules": db.query(Filleule).count(),
        "referents": db.query(Correspondant).count(),
        "ecoles": db.query(Etablissement).count(),
        "localites": db.query(Localite).count(),
        "parrains": db.query(Parrain).count(),
        "parrainages": db.query(Parrainage).count(),
        "documents": db.query(Document).count(),
    }

    db.close()
    return stats


async def get_city_origin_stats():
    db: Session = SessionLocal()
    rows = (
        db.query(Filleule.id_filleule, Filleule.prenom, Filleule.nom, Filleule.ville)
        .filter(Filleule.ville.isnot(None))
        .filter(func.trim(Filleule.ville) != "")
        .all()
    )

    localites = db.query(Localite).all()
    db.close()

    coords = {l.nom: {"lat": l.latitude, "lon": l.longitude} for l in localites}
    localite_map = {}
    for localite in localites:
        localite_map[normalize_city_name(localite.nom)] = localite.nom
        if localite.aliases:
            for alias in localite.aliases.split(","):
                alias = alias.strip()
                if alias:
                    localite_map[normalize_city_name(alias)] = localite.nom
    city_map: dict[str, dict] = {}
    for filleule_id, prenom, nom, ville in rows:
        ville = ville.strip() if isinstance(ville, str) else ville
        if not ville:
            continue
        entry = city_map.setdefault(
            ville,
            {"name": ville, "count": 0, "filleules": []},
        )
        entry["count"] += 1
        entry["filleules"].append(
            {
                "id": filleule_id,
                "prenom": prenom or "",
                "nom": nom or "",
            }
        )

    for entry in city_map.values():
        entry["filleules"].sort(key=lambda item: (item["nom"].lower(), item["prenom"].lower()))

    cities = sorted(city_map.values(), key=lambda item: item["name"].lower())
    missing = []
    for entry in cities:
        normalized = normalize_city_name(entry["name"])
        canonical = localite_map.get(normalized, entry["name"])
        coord = coords.get(canonical)
        if coord and "lat" in coord and "lon" in coord:
            try:
                entry["lat"] = float(coord["lat"])
                entry["lon"] = float(coord["lon"])
            except (TypeError, ValueError):
                missing.append(entry["name"])
        else:
            missing.append(entry["name"])

    return {"cities": cities, "missing": missing}

async def get_chart_data():
    db = SessionLocal()

    # 1. Nombre de filleuls par établissement
    filleuls_par_etab = (
        db.query(Etablissement.nom, func.count(Filleule.id_filleule))
        .join(Filleule, Filleule.etablissement_id == Etablissement.id_etablissement)
        .group_by(Etablissement.nom)
        .all()
    )

    # 2. Nombre de parrainages par année
    parrainages_par_annee = (
        db.query(func.extract('year', Parrainage.date_debut).label("annee"),
                 func.count(Parrainage.id_parrainage))
        .filter(Parrainage.date_debut.isnot(None))
        .group_by("annee")
        .order_by("annee")
        .all()
    )

    # Liste des établissements
    etablissements = db.query(Etablissement.nom, Etablissement.id_etablissement).all()

    # Liste des années présentes dans les parrainages
    annees = (
        db.query(func.extract('year', Parrainage.date_debut))
        .filter(Parrainage.date_debut.isnot(None))
        .distinct()
        .all()
    )
    annees = [int(a[0]) for a in annees if a[0] is not None]

    # 3. Répartition des filleuls par niveau scolaire
    latest_scolarite = (
        db.query(Scolarite.id_filleule, func.max(Scolarite.id_scolarite).label("max_id"))
        .group_by(Scolarite.id_filleule)
        .subquery()
    )
    ScolariteLatest = aliased(Scolarite)
    niveaux = (
        db.query(ScolariteLatest.niveau, func.count(ScolariteLatest.id_scolarite))
        .join(latest_scolarite, ScolariteLatest.id_scolarite == latest_scolarite.c.max_id)
        .group_by(ScolariteLatest.niveau)
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


async def get_filiere_stats():
    db: Session = SessionLocal()

    latest_scolarite = (
        db.query(Scolarite.id_filleule, func.max(Scolarite.id_scolarite).label("max_id"))
        .group_by(Scolarite.id_filleule)
        .subquery()
    )
    ScolariteLatest = aliased(Scolarite)
    rows = (
        db.query(ScolariteLatest.filiere, func.count(ScolariteLatest.id_scolarite))
        .join(latest_scolarite, ScolariteLatest.id_scolarite == latest_scolarite.c.max_id)
        .filter(ScolariteLatest.filiere.isnot(None))
        .filter(func.trim(ScolariteLatest.filiere) != "")
        .group_by(ScolariteLatest.filiere)
        .order_by(func.count(ScolariteLatest.id_scolarite).desc(), ScolariteLatest.filiere)
        .all()
    )

    db.close()
    return [{"name": filiere, "count": count} for filiere, count in rows]
