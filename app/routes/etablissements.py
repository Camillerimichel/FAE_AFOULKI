from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.etablissement import ETABLISSEMENT_TYPES, Etablissement
from app.schemas.etablissement import EtablissementCreate, EtablissementResponse

router = APIRouter(prefix="/etablissements", tags=["Etablissements"])
templates = Jinja2Templates(directory="app/templates")


# --------------------------------------------------------
#            ROUTES HTML — PROTÉGÉES SESSION
# --------------------------------------------------------

@router.get("/html")
def liste_etablissements_html(request: Request, db: Session = Depends(get_db)):
    """
    Affiche la liste des établissements (HTML)
    """
    if not request.state.user:
        return RedirectResponse("/auth/login")

    data = db.query(Etablissement).all()
    return templates.TemplateResponse(
        "etablissements/list.html",
        {"request": request, "etablissements": data},
    )


@router.get("/html/{etablissement_id}")
def detail_etablissement_html(etablissement_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Affiche le détail d'un établissement (HTML)
    """
    if not request.state.user:
        return RedirectResponse("/auth/login")

    record = db.query(Etablissement).filter(Etablissement.id_etablissement == etablissement_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Établissement non trouvé")

    return templates.TemplateResponse(
        "etablissements/detail.html",
        {"request": request, "etablissement": record},
    )


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
    if data.type not in (None, *ETABLISSEMENT_TYPES):
        raise HTTPException(status_code=400, detail="Type d'établissement invalide")

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

    if data.type not in (None, *ETABLISSEMENT_TYPES):
        raise HTTPException(status_code=400, detail="Type d'établissement invalide")

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
