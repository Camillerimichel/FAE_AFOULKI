from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models.suivisocial import SuiviSocial
from app.schemas.suivisocial import SuiviSocialCreate, SuiviSocialResponse

router = APIRouter(prefix="/suivisocial", tags=["Suivi Social"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def suivisocial_html(request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse("/auth/login")

    suivis = (
        db.query(SuiviSocial)
        .options(joinedload(SuiviSocial.filleule))
        .order_by(SuiviSocial.date_suivi.desc(), SuiviSocial.id_suivi.desc())
        .all()
    )
    return templates.TemplateResponse(
        "suivisocial/list.html",
        {"request": request, "suivis": suivis},
    )


@router.get("/api", response_model=list[SuiviSocialResponse])
def get_all_suivis(db: Session = Depends(get_db)):
    return db.query(SuiviSocial).all()


@router.get("/api/{suivi_id}", response_model=SuiviSocialResponse)
def get_suivi(suivi_id: int, db: Session = Depends(get_db)):
    record = db.query(SuiviSocial).filter(SuiviSocial.id_suivi == suivi_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Suivi social introuvable")
    return record


@router.post("/api", response_model=SuiviSocialResponse)
def create_suivi(data: SuiviSocialCreate, db: Session = Depends(get_db)):
    record = SuiviSocial(**data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.put("/api/{suivi_id}", response_model=SuiviSocialResponse)
def update_suivi(suivi_id: int, data: SuiviSocialCreate, db: Session = Depends(get_db)):
    record = db.query(SuiviSocial).filter(SuiviSocial.id_suivi == suivi_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Suivi social introuvable")

    for key, value in data.dict().items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/api/{suivi_id}")
def delete_suivi(suivi_id: int, db: Session = Depends(get_db)):
    record = db.query(SuiviSocial).filter(SuiviSocial.id_suivi == suivi_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Suivi social introuvable")

    db.delete(record)
    db.commit()
    return {"message": "Suivi social supprimé"}
