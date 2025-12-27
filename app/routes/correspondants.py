from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.correspondant import Correspondant
from app.models.filleule import Filleule
from app.schemas.correspondant import CorrespondantCreate, CorrespondantResponse

router = APIRouter(prefix="/correspondants", tags=["Référents"])
templates = Jinja2Templates(directory="app/templates")


# --------------------------------------------------------
#            ROUTES HTML — PROTÉGÉES SESSION
# --------------------------------------------------------

@router.get("/html")
def liste_correspondants_html(request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse("/auth/login")

    data = db.query(Correspondant).all()
    rows = (
        db.query(Filleule.id_correspondant, func.count(Filleule.id_filleule))
        .filter(Filleule.id_correspondant.isnot(None))
        .group_by(Filleule.id_correspondant)
        .all()
    )
    counts = {row[0]: row[1] for row in rows}
    return templates.TemplateResponse(
        "correspondants/list.html",
        {"request": request, "correspondants": data, "correspondant_counts": counts},
    )


@router.get("/html/{correspondant_id}")
def detail_correspondant_html(correspondant_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.state.user:
        return RedirectResponse("/auth/login")

    record = (
        db.query(Correspondant)
        .filter(Correspondant.id_correspondant == correspondant_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Référent introuvable")

    filleules = (
        db.query(Filleule)
        .filter(Filleule.id_correspondant == record.id_correspondant)
        .order_by(Filleule.id_filleule.desc())
        .all()
    )

    return templates.TemplateResponse(
        "correspondants/detail.html",
        {"request": request, "correspondant": record, "filleules": filleules},
    )


@router.get("/", response_model=list[CorrespondantResponse])
def get_correspondants(db: Session = Depends(get_db)):
    return db.query(Correspondant).all()


@router.get("/{correspondant_id}", response_model=CorrespondantResponse)
def get_correspondant(correspondant_id: int, db: Session = Depends(get_db)):
    record = db.query(Correspondant).filter(Correspondant.id_correspondant == correspondant_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Référent introuvable")
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
        raise HTTPException(status_code=404, detail="Référent introuvable")

    for key, value in data.dict().items():
        setattr(record, key, value)

    db.commit()
    db.refresh(record)
    return record


@router.delete("/{correspondant_id}")
def delete_correspondant(correspondant_id: int, db: Session = Depends(get_db)):
    record = db.query(Correspondant).filter(Correspondant.id_correspondant == correspondant_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Référent introuvable")

    db.delete(record)
    db.commit()
    return {"message": "Référent supprimé"}
