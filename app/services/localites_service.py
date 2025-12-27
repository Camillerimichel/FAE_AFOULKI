import re

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.filleule import Filleule
from app.models.localite import Localite


LOCALITES_SEED = [
    {
        "nom": "Essaouira",
        "latitude": 31.5085,
        "longitude": -9.7595,
        "aliases": "",
    },
    {
        "nom": "Ounagha",
        "latitude": 31.64,
        "longitude": -9.53,
        "aliases": "",
    },
    {
        "nom": "Smimou",
        "latitude": 31.21,
        "longitude": -9.71,
        "aliases": "Smimmou",
    },
    {
        "nom": "Tamanar",
        "latitude": 30.91,
        "longitude": -9.68,
        "aliases": "",
    },
    {
        "nom": "Had Draa",
        "latitude": 31.21,
        "longitude": -9.43,
        "aliases": "Haad Dra, Haad Draa",
    },
    {
        "nom": "Tidzi",
        "latitude": 31.38,
        "longitude": -9.35,
        "aliases": "",
    },
    {
        "nom": "Ain Hjar",
        "latitude": 31.12,
        "longitude": -9.52,
        "aliases": "Ain Hjer, Annexe Ain Hjar - Sidi Yahya, Annexe Ain Hjar( sidi yahya)",
    },
    {
        "nom": "Ghazoua",
        "latitude": 31.48,
        "longitude": -9.68,
        "aliases": "",
    },
    {
        "nom": "Akermaoud",
        "latitude": 31.32,
        "longitude": -9.2,
        "aliases": "Akermoud, Akermaoud",
    },
    {
        "nom": "Tafedna",
        "latitude": 31.05,
        "longitude": -9.83,
        "aliases": "",
    },
    {
        "nom": "Talmest",
        "latitude": 31.47,
        "longitude": -9.3,
        "aliases": "",
    },
    {
        "nom": "Lamgadma",
        "latitude": 31.26,
        "longitude": -9.6,
        "aliases": "",
    },
    {
        "nom": "Moulay Bouzerktoun",
        "latitude": 31.7,
        "longitude": -9.88,
        "aliases": "Moulay",
    },
    {
        "nom": "Adarzane",
        "latitude": 31.15,
        "longitude": -9.26,
        "aliases": "",
    },
    {
        "nom": "Ait Debaba Elhaimar",
        "latitude": 31.18,
        "longitude": -9.31,
        "aliases": "",
    },
    {
        "nom": "Ait Hmad El Fijel",
        "latitude": 31.14,
        "longitude": -9.29,
        "aliases": "",
    },
    {
        "nom": "Er-Riyada",
        "latitude": 31.3,
        "longitude": -9.55,
        "aliases": "Erreyade",
    },
    {
        "nom": "Hal Ben Mellel",
        "latitude": 31.27,
        "longitude": -9.48,
        "aliases": "Halbenmel",
    },
    {
        "nom": "Meji",
        "latitude": 31.09,
        "longitude": -9.41,
        "aliases": "",
    },
    {
        "nom": "Areb",
        "latitude": 31.24,
        "longitude": -9.36,
        "aliases": "",
    },
]


def ensure_localites_seed() -> None:
    db: Session = SessionLocal()
    try:
        existing = {row.nom: row for row in db.query(Localite).all()}
        to_add = []
        for item in LOCALITES_SEED:
            row = existing.get(item["nom"])
            if row:
                row.latitude = item["latitude"]
                row.longitude = item["longitude"]
                row.aliases = item["aliases"]
                continue
            to_add.append(
                Localite(
                    nom=item["nom"],
                    latitude=item["latitude"],
                    longitude=item["longitude"],
                    aliases=item["aliases"],
                )
            )
        if to_add:
            db.add_all(to_add)
        if to_add or existing:
            db.commit()
    finally:
        db.close()


def normalize_localite_value(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return " ".join(cleaned.split()).strip()


def build_localites_map(localites: list[Localite]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for localite in localites:
        variants = [localite.nom]
        if localite.aliases:
            variants.extend([item.strip() for item in localite.aliases.split(",") if item.strip()])
        for name in variants:
            key = normalize_localite_value(name)
            if key:
                mapping[key] = localite.nom
    return mapping


def resolve_localite_name(value: str | None, mapping: dict[str, str]) -> str | None:
    if not value:
        return None
    key = normalize_localite_value(value)
    if not key:
        return None
    return mapping.get(key)


def ensure_filleule_ville_mapping() -> None:
    db: Session = SessionLocal()
    try:
        localites = db.query(Localite).all()
        if not localites:
            return
        mapping = build_localites_map(localites)
        updated = 0
        for filleule in db.query(Filleule).filter(Filleule.ville.isnot(None)).all():
            resolved = resolve_localite_name(filleule.ville, mapping)
            if resolved and filleule.ville != resolved:
                filleule.ville = resolved
                updated += 1
        if updated:
            db.commit()
    finally:
        db.close()
