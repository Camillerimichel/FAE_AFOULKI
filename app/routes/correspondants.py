from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.correspondant import Correspondant
from app.schemas.correspondant import CorrespondantCreate, CorrespondantResponse

router = APIRouter(prefix="/correspondants", tags=["Correspondants"])


@router.get("/", response_model=list[CorrespondantResponse])
def get_correspondants(db: Session = Depends(get_db)):
    return db.query(Correspondant).all()


@router.get("/{correspondant_id}", response_model=CorrespondantResponse)
def get_correspondant(correspondant_id: int, db: Session = Depends(get_db)):
    record = db.query(Correspondant).filter(Correspondant.id_correspondant == correspondant_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Correspondant introuvable")
    return record


@router.post("/", response_model=CorrespondantResponse)
def create_correspondant(data: CorrespondantCreate, db: Session = Depends(get_db)):
    record = Correspondant(**data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{correspondant_id}", response_model=CorrespondantResponse)
def update_correspondant(correspondant_id: int, data: CorrespondantCreate, db: Session = Depends(get_db)):
    record = db.query(Correspondant).filter(Correspondant.id_correspondant == correspondant_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Correspondant introuvable")

    for key, value in data.dict().items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{correspondant_id}")
def delete_correspondant(correspondant_id: int, db: Session = Depends(get_db)):
    record = db.query(Correspondant).filter(Correspondant.id_correspondant == correspondant_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Correspondant introuvable")

    db.delete(record)
    db.commit()
    return {"message": "Correspondant supprimé"}
