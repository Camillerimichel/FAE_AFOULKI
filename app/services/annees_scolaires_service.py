from datetime import date

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.annee_scolaire import AnneeScolaire


def _build_periode(start_year: int) -> str:
    return f"{start_year}/{start_year + 1}"


def ensure_annees_scolaires_seed(start_year: int = 2010) -> None:
    db: Session = SessionLocal()
    try:
        current_year = date.today().year
        existing = {row.periode for row in db.query(AnneeScolaire).all()}

        to_add = []
        for year in range(start_year, current_year + 1):
            periode = _build_periode(year)
            if periode not in existing:
                to_add.append(AnneeScolaire(periode=periode))

        if to_add:
            db.add_all(to_add)
            db.commit()
    finally:
        db.close()
