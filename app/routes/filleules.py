from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.filleule import Filleule
from app.schemas.filleule import FilleuleCreate, FilleuleResponse

router = APIRouter(prefix="/filleules", tags=["Filleules"])

templates = Jinja2Templates(directory="app/templates")


# --------------------------------------------------------
#                    ROUTES HTML PROTÉGÉES
# --------------------------------------------------------

@router.get("/html")
def liste_filleules_html(request: Request, db: Session = Depends(get_db)):
    """
    Affiche la liste des filleules en HTML.
    Page protégée : nécessite une session utilisateur.
    """
    if not request.state.user:
        return RedirectResponse("/auth/login")

    data = db.query(Filleule).all()
    return templates.TemplateResponse(
        "filleules/list.html",
        {"request": request, "filleules": data}
    )


@router.get("/html/{filleule_id}")
def detail_filleule_html(filleule_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Affiche la fiche détaillée d'une filleule.
    Page protégée : nécessite une session utilisateur.
    """
    if not request.state.user:
        return RedirectResponse("/auth/login")

    f = db.query(Filleule).filter(Filleule.id_filleule == filleule_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Filleule non trouvée")

    return templates.TemplateResponse(
        "filleules/detail.html",
        {"request": request, "filleule": f}
    )


# --------------------------------------------------------
#                     API REST CRUD
# --------------------------------------------------------

@router.get("/", response_model=list[FilleuleResponse])
def get_filleules(db: Session = Depends(get_db)):
    """
    Retourne toutes les filleules (API JSON)
    """
    return db.query(Filleule).all()


@router.get("/{filleule_id}", response_model=FilleuleResponse)
def get_filleule(filleule_id: int, db: Session = Depends(get_db)):
    """
    Retourne une filleule spécifique (API JSON)
    """
    filleule = db.query(Filleule).filter(Filleule.id_filleule == filleule_id).first()
    if not filleule:
        raise HTTPException(status_code=404, detail="Filleule non trouvée")
    return filleule


@router.post("/", response_model=FilleuleResponse)
def create_filleule(data: FilleuleCreate, db: Session = Depends(get_db)):
    """
    Crée une nouvelle filleule (API JSON)
    """
    new_filleule = Filleule(**data.dict())
    db.add(new_filleule)
    db.commit()
    db.refresh(new_filleule)
    return new_filleule


@router.put("/{filleule_id}", response_model=FilleuleResponse)
def update_filleule(filleule_id: int, data: FilleuleCreate, db: Session = Depends(get_db)):
    """
    Modifie une filleule (API JSON)
    """
    filleule = db.query(Filleule).filter(Filleule.id_filleule == filleule_id).first()
    if not filleule:
        raise HTTPException(status_code=404, detail="Filleule non trouvée")

    for key, value in data.dict().items():
        setattr(filleule, key, value)

    db.commit()
    db.refresh(filleule)
    return filleule


@router.delete("/{filleule_id}")
def delete_filleule(filleule_id: int, db: Session = Depends(get_db)):
    """
    Supprime une filleule (API JSON)
    """
    filleule = db.query(Filleule).filter(Filleule.id_filleule == filleule_id).first()
    if not filleule:
        raise HTTPException(status_code=404, detail="Filleule non trouvée")

    db.delete(filleule)
    db.commit()
    return {"message": "Filleule supprimée"}
