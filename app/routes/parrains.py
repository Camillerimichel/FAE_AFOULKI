from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.parrain import Parrain
from app.schemas.parrain import ParrainCreate, ParrainResponse

router = APIRouter(prefix="/parrains", tags=["Parrains"])

templates = Jinja2Templates(directory="app/templates")


# --------------------------------------------------------
#            ROUTES HTML — PROTÉGÉES SESSION
# --------------------------------------------------------

@router.get("/html")
def liste_parrains_html(request: Request, db: Session = Depends(get_db)):
    """
    Affiche la liste des parrains (HTML)
    """
    if not request.state.user:
        return RedirectResponse("/auth/login")

    data = db.query(Parrain).all()
    return templates.TemplateResponse(
        "parrains/list.html",
        {"request": request, "parrains": data}
    )


@router.get("/html/{parrain_id}")
def detail_parrain_html(parrain_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Affiche le détail d'un parrain (HTML)
    """
    if not request.state.user:
        return RedirectResponse("/auth/login")

    parrain = db.query(Parrain).filter(Parrain.id_parrain == parrain_id).first()
    if not parrain:
        raise HTTPException(status_code=404, detail="Parrain non trouvé")

    return templates.TemplateResponse(
        "parrains/detail.html",
        {"request": request, "parrain": parrain}
    )


# --------------------------------------------------------
#                      API CRUD JSON
# --------------------------------------------------------

@router.get("/", response_model=list[ParrainResponse])
def get_parrains(db: Session = Depends(get_db)):
    return db.query(Parrain).all()


@router.get("/{parrain_id}", response_model=ParrainResponse)
def get_parrain(parrain_id: int, db: Session = Depends(get_db)):
    parrain = db.query(Parrain).filter(Parrain.id_parrain == parrain_id).first()
    if not parrain:
        raise HTTPException(status_code=404, detail="Parrain non trouvé")
    return parrain


@router.post("/", response_model=ParrainResponse)
def create_parrain(data: ParrainCreate, db: Session = Depends(get_db)):
    nouveau = Parrain(**data.dict())
    db.add(nouveau)
    db.commit()
    db.refresh(nouveau)
    return nouveau


@router.put("/{parrain_id}", response_model=ParrainResponse)
def update_parrain(parrain_id: int, data: ParrainCreate, db: Session = Depends(get_db)):
    parrain = db.query(Parrain).filter(Parrain.id_parrain == parrain_id).first()
    if not parrain:
        raise HTTPException(status_code=404, detail="Parrain non trouvé")

    for key, value in data.dict().items():
        setattr(parrain, key, value)

    db.commit()
    db.refresh(parrain)
    return parrain


@router.delete("/{parrain_id}")
def delete_parrain(parrain_id: int, db: Session = Depends(get_db)):
    parrain = db.query(Parrain).filter(Parrain.id_parrain == parrain_id).first()
    if not parrain:
        raise HTTPException(status_code=404, detail="Parrain non trouvé")

    db.delete(parrain)
    db.commit()
    return {"message": "Parrain supprimé"}

