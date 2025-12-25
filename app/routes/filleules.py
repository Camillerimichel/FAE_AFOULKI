from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.filleule import Filleule
from app.models.parrainage import Parrainage
from app.models.scolarite import Scolarite
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

    data = (
        db.query(Filleule)
        .options(
            joinedload(Filleule.scolarites).joinedload(Scolarite.etablissement),
            joinedload(Filleule.scolarites).joinedload(Scolarite.annee_scolaire_ref),
        )
        .all()
    )

    def periode_from_scolarite(record: Scolarite) -> str | None:
        if record.annee_scolaire_ref and record.annee_scolaire_ref.periode:
            return record.annee_scolaire_ref.periode
        return record.annee_scolaire

    def start_year_key(periode: str | None) -> int:
        if not periode:
            return -1
        cleaned = periode.replace("-", "/")
        first = cleaned.split("/", 1)[0]
        digits = "".join(ch for ch in first if ch.isdigit())
        if len(digits) < 4:
            return -1
        try:
            return int(digits[:4])
        except ValueError:
            return -1

    recent_scolarite: dict[int, dict[str, str]] = {}
    for filleule in data:
        best_key = (-1, -1)
        best_item: dict[str, str] | None = None
        for record in filleule.scolarites:
            periode = periode_from_scolarite(record)
            key = (start_year_key(periode), record.id_scolarite or 0)
            if key > best_key:
                best_key = key
                best_item = {
                    "periode": periode or "-",
                    "etablissement": record.etablissement.nom if record.etablissement else "-",
                }
        if best_item:
            recent_scolarite[filleule.id_filleule] = best_item

    return templates.TemplateResponse(
        "filleules/list.html",
        {"request": request, "filleules": data, "recent_scolarite": recent_scolarite}
    )


@router.get("/html/{filleule_id}")
def detail_filleule_html(filleule_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Affiche la fiche détaillée d'une filleule.
    Page protégée : nécessite une session utilisateur.
    """
    if not request.state.user:
        return RedirectResponse("/auth/login")

    f = (
        db.query(Filleule)
        .options(
            joinedload(Filleule.scolarites).joinedload(Scolarite.etablissement),
            joinedload(Filleule.scolarites).joinedload(Scolarite.annee_scolaire_ref),
            joinedload(Filleule.parrainages).joinedload(Parrainage.parrain),
        )
        .filter(Filleule.id_filleule == filleule_id)
        .first()
    )
    if not f:
        raise HTTPException(status_code=404, detail="Filleule non trouvée")

    def periode_from_scolarite(record: Scolarite) -> str | None:
        if record.annee_scolaire_ref and record.annee_scolaire_ref.periode:
            return record.annee_scolaire_ref.periode
        return record.annee_scolaire

    def start_year_key(periode: str | None) -> int:
        if not periode:
            return -1
        cleaned = periode.replace("-", "/")
        first = cleaned.split("/", 1)[0]
        digits = "".join(ch for ch in first if ch.isdigit())
        if len(digits) < 4:
            return -1
        try:
            return int(digits[:4])
        except ValueError:
            return -1

    scolarites = sorted(
        f.scolarites,
        key=lambda record: (start_year_key(periode_from_scolarite(record)), record.id_scolarite or 0),
        reverse=True,
    )

    parrains = []
    seen_parrains = set()
    for parrainage in f.parrainages:
        parrain = parrainage.parrain
        if parrain and parrain.id_parrain not in seen_parrains:
            seen_parrains.add(parrain.id_parrain)
            parrains.append(parrain)

    return templates.TemplateResponse(
        "filleules/detail.html",
        {"request": request, "filleule": f, "scolarites": scolarites, "parrains": parrains}
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
