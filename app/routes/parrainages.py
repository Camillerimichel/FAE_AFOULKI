from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.parrainage import Parrainage
from app.schemas.parrainage import ParrainageCreate, ParrainageResponse

router = APIRouter(prefix="/parrainages", tags=["Parrainages"])


@router.get("/", response_model=list[ParrainageResponse])
def get_parrainages(db: Session = Depends(get_db)):
    return db.query(Parrainage).all()


@router.get("/{parrainage_id}", response_model=ParrainageResponse)
def get_parrainage(parrainage_id: int, db: Session = Depends(get_db)):
    record = db.query(Parrainage).filter(Parrainage.id_parrainage == parrainage_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Parrainage introuvable")
    return record


@router.post("/", response_model=ParrainageResponse)
def create_parrainage(data: ParrainageCreate, db: Session = Depends(get_db)):
    record = Parrainage(**data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{parrainage_id}", response_model=ParrainageResponse)
def update_parrainage(parrainage_id: int, data: ParrainageCreate, db: Session = Depends(get_db)):
    record = db.query(Parrainage).filter(Parrainage.id_parrainage == parrainage_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Parrainage introuvable")

    for key, value in data.dict().items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{parrainage_id}")
def delete_parrainage(parrainage_id: int, db: Session = Depends(get_db)):
    record = db.query(Parrainage).filter(Parrainage.id_parrainage == parrainage_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Parrainage introuvable")

    db.delete(record)
    db.commit()
    return {"message": "Parrainage supprimé"}
