from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.annee_scolaire import AnneeScolaire
from app.models.filleule import Filleule
from app.models.scolarite import Scolarite

# Import models to ensure SQLAlchemy relationships are registered.
import app.models.correspondant  # noqa: F401
import app.models.document  # noqa: F401
import app.models.etablissement  # noqa: F401
import app.models.parrain  # noqa: F401
import app.models.parrainage  # noqa: F401
import app.models.role  # noqa: F401
import app.models.suivisocial  # noqa: F401
import app.models.typedocument  # noqa: F401
import app.models.user  # noqa: F401


def main() -> None:
    periode = "2023/2024"
    db: Session = SessionLocal()

    annee = db.query(AnneeScolaire).filter(AnneeScolaire.periode == periode).first()
    if not annee:
        db.close()
        print(f"Annee scolaire introuvable: {periode}")
        return

    existing_rows = (
        db.query(Scolarite.id_filleule)
        .filter(
            or_(
                Scolarite.id_annee_scolaire == annee.id_annee_scolaire,
                Scolarite.annee_scolaire == periode,
            )
        )
        .all()
    )
    existing_ids = {row[0] for row in existing_rows if row[0] is not None}

    filleules = db.query(Filleule).all()
    created = 0
    skipped = 0
    missing_referent = 0
    backfilled = 0

    backfill_rows = (
        db.query(Scolarite, Filleule.id_correspondant)
        .join(Filleule, Filleule.id_filleule == Scolarite.id_filleule)
        .filter(
            or_(
                Scolarite.id_annee_scolaire == annee.id_annee_scolaire,
                Scolarite.annee_scolaire == periode,
            ),
            or_(Scolarite.referent_a.is_(None), Scolarite.referent_a == ""),
            Filleule.id_correspondant.isnot(None),
        )
        .all()
    )
    for scolarite, ref_id in backfill_rows:
        scolarite.referent_a = str(ref_id)
        backfilled += 1

    for filleule in filleules:
        if filleule.id_filleule in existing_ids:
            skipped += 1
            continue

        referent_a = str(filleule.id_correspondant) if filleule.id_correspondant else None
        if not referent_a:
            missing_referent += 1

        scolarite = Scolarite(
            id_filleule=filleule.id_filleule,
            id_etablissement=filleule.etablissement_id,
            id_annee_scolaire=annee.id_annee_scolaire,
            annee_scolaire=annee.periode,
            referent_a=referent_a,
        )
        db.add(scolarite)
        created += 1

    db.commit()
    db.close()

    print(f"Crees: {created}")
    print(f"Ignores (deja existants): {skipped}")
    print(f"Sans referent A: {missing_referent}")
    print(f"Referents A reatribues: {backfilled}")


if __name__ == "__main__":
    main()
