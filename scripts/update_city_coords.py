import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.filleule import Filleule
from app.services.stats_service import CITY_COORDS_PATH, normalize_city_name


def geocode_city(city: str) -> dict | None:
    query = f"{city}, Essaouira, Morocco"
    params = urllib.parse.urlencode({"format": "json", "limit": 1, "q": query})
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "FAE_AFOULKI/1.0 (contact@fae.local)"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not data:
        return None
    return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}


def load_existing() -> dict:
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


def main() -> None:
    coords = load_existing()

    db: Session = SessionLocal()
    rows = (
        db.query(Filleule.ville)
        .filter(Filleule.ville.isnot(None))
        .distinct()
        .all()
    )
    db.close()

    cities = [row[0] for row in rows if row[0] and row[0].strip()]
    missing = []

    for city in sorted(set(cities), key=str.lower):
        key = normalize_city_name(city)
        if key in coords:
            continue
        try:
            result = geocode_city(city)
        except Exception:
            result = None
        if result:
            coords[key] = result
        else:
            missing.append(city)
        time.sleep(1.1)

    CITY_COORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CITY_COORDS_PATH.open("w", encoding="utf-8") as file_obj:
        json.dump(coords, file_obj, ensure_ascii=False, indent=2)

    if missing:
        print("Villes sans coordonnees:", ", ".join(missing))
    else:
        print("Toutes les villes sont geocodees.")


if __name__ == "__main__":
    main()
