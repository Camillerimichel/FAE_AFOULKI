from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.suivisocial import SuiviSocial
from app.schemas.suivisocial import SuiviSocialCreate, SuiviSocialResponse

router = APIRouter(prefix="/suivisocial", tags=["Suivi Social"])


@router.get("/", response_model=list[SuiviSocialResponse])
def get_all_suivis(db: Session = Depends(get_db)):
    return db.query(SuiviSocial).all()


@router.get("/{suivi_id}", response_model=SuiviSocialResponse)
def get_suivi(suivi_id: int, db: Session = Depends(get_db)):
    record = db.query(SuiviSocial).filter(SuiviSocial.id_suivi == suivi_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Suivi social introuvable")
    return record


@router.post("/", response_model=SuiviSocialResponse)
def create_suivi(data: SuiviSocialCreate, db: Session = Depends(get_db)):
    record = SuiviSocial(**data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/{suivi_id}", response_model=SuiviSocialResponse)
def update_suivi(suivi_id: int, data: SuiviSocialCreate, db: Session = Depends(get_db)):
    record = db.query(SuiviSocial).filter(SuiviSocial.id_suivi == suivi_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Suivi social introuvable")

    for key, value in data.dict().items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{suivi_id}")
def delete_suivi(suivi_id: int, db: Session = Depends(get_db)):
    record = db.query(SuiviSocial).filter(SuiviSocial.id_suivi == suivi_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Suivi social introuvable")

    db.delete(record)
    db.commit()
    return {"message": "Suivi social supprimé"}
