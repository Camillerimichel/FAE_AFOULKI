from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates

from app.database import get_db
from app.models.scolarite import Scolarite
from app.models.annee_scolaire import AnneeScolaire
from app.schemas.scolarite import ScolariteCreate, ScolariteResponse

router = APIRouter(prefix="/scolarite", tags=["Scolarité"])

# Templates
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_model=list[ScolariteResponse])
def get_all_scolarite(db: Session = Depends(get_db)):
    return db.query(Scolarite).all()


# ----------------------------------------------------------------------
#   ROUTE HTML POUR ÉVITER L'ERREUR /scolarite/html
# ----------------------------------------------------------------------
@router.get("/html")
def scolarite_html(request: Request):
    return templates.TemplateResponse(
        "scolarite_html.html",
        {"request": request}
    )
# ----------------------------------------------------------------------


@router.get("/{scolarite_id}", response_model=ScolariteResponse)
def get_scolarite(scolarite_id: int, db: Session = Depends(get_db)):
    record = db.query(Scolarite).filter(Scolarite.id_scolarite == scolarite_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Enregistrement de scolarité introuvable")
    return record


@router.post("/", response_model=ScolariteResponse)
def create_scolarite(data: ScolariteCreate, db: Session = Depends(get_db)):
    payload = data.dict()
    annee_id = payload.get("id_annee_scolaire")
    if annee_id and not payload.get("annee_scolaire"):
        annee = (
            db.query(AnneeScolaire)
            .filter(AnneeScolaire.id_annee_scolaire == annee_id)
            .first()
        )
        if not annee:
            raise HTTPException(status_code=400, detail="Année scolaire invalide")
        payload["annee_scolaire"] = annee.periode

    record = Scolarite(**payload)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{scolarite_id}", response_model=ScolariteResponse)
def update_scolarite(scolarite_id: int, data: ScolariteCreate, db: Session = Depends(get_db)):
    record = db.query(Scolarite).filter(Scolarite.id_scolarite == scolarite_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Enregistrement de scolarité introuvable")

    payload = data.dict()
    annee_id = payload.get("id_annee_scolaire")
    if annee_id and not payload.get("annee_scolaire"):
        annee = (
            db.query(AnneeScolaire)
            .filter(AnneeScolaire.id_annee_scolaire == annee_id)
            .first()
        )
        if not annee:
            raise HTTPException(status_code=400, detail="Année scolaire invalide")
        payload["annee_scolaire"] = annee.periode

    for key, value in payload.items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{scolarite_id}")
def delete_scolarite(scolarite_id: int, db: Session = Depends(get_db)):
    record = db.query(Scolarite).filter(Scolarite.id_scolarite == scolarite_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Enregistrement de scolarité introuvable")

    db.delete(record)
    db.commit()
    return {"message": "Scolarité supprimée"}
