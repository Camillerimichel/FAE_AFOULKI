from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.etablissement import Etablissement
from app.schemas.etablissement import EtablissementCreate, EtablissementResponse

router = APIRouter(prefix="/etablissements", tags=["Etablissements"])


@router.get("/", response_model=list[EtablissementResponse])
def get_etablissements(db: Session = Depends(get_db)):
    return db.query(Etablissement).all()


@router.get("/{etablissement_id}", response_model=EtablissementResponse)
def get_etablissement(etablissement_id: int, db: Session = Depends(get_db)):
    record = db.query(Etablissement).filter(Etablissement.id_etablissement == etablissement_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Établissement non trouvé")
    return record


@router.post("/", response_model=EtablissementResponse)
def create_etablissement(data: EtablissementCreate, db: Session = Depends(get_db)):
    record = Etablissement(**data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{etablissement_id}", response_model=EtablissementResponse)
def update_etablissement(etablissement_id: int, data: EtablissementCreate, db: Session = Depends(get_db)):
    record = db.query(Etablissement).filter(Etablissement.id_etablissement == etablissement_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Établissement non trouvé")

    for key, value in data.dict().items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{etablissement_id}")
def delete_etablissement(etablissement_id: int, db: Session = Depends(get_db)):
    record = db.query(Etablissement).filter(Etablissement.id_etablissement == etablissement_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Établissement non trouvé")

    db.delete(record)
    db.commit()
    return {"message": "Établissement supprimé"}
