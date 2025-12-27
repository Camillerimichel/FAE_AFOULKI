import os
import shutil
from pathlib import Path

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import BASE_DIR, get_db
from app.models.parrain import Parrain
from app.models.parrainage import Parrainage
from app.schemas.parrain import ParrainCreate, ParrainResponse

router = APIRouter(prefix="/parrains", tags=["Parrains"])

templates = Jinja2Templates(directory="app/templates")
DOCUMENTS_DIR = BASE_DIR / "Documents" / "Parrains"


def remove_parrain_assets(parrain: Parrain) -> None:
    if parrain.photo:
        path = Path(parrain.photo)
        if not path.is_absolute():
            path = BASE_DIR / path
        if path.exists():
            os.remove(path)

    parrain_dir = DOCUMENTS_DIR / str(parrain.id_parrain)
    if parrain_dir.exists():
        shutil.rmtree(parrain_dir)


# --------------------------------------------------------
#            ROUTES HTML — PROTÉGÉES SESSION
# --------------------------------------------------------

@router.get("/html")
def liste_parrains_html(
    request: Request,
    sans_filleules: int | None = None,
    db: Session = Depends(get_db),
):
    """
    Affiche la liste des parrains (HTML)
    """
    if not request.state.user:
        return RedirectResponse("/auth/login")

    without_filleules_query = db.query(Parrain).filter(~Parrain.parrainages.any())
    count_without_filleules = without_filleules_query.count()

    query = db.query(Parrain)
    if sans_filleules:
        query = without_filleules_query
    data = query.all()
    return templates.TemplateResponse(
        "parrains/list.html",
        {
            "request": request,
            "parrains": data,
            "showing_without_filleules": bool(sans_filleules),
            "count_without_filleules": count_without_filleules,
        }
    )


@router.get("/html/{parrain_id}/vcard")
def export_parrain_vcard(parrain_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Exporte la fiche parrain au format vCard.
    """
    if not request.state.user:
        return RedirectResponse("/auth/login")

    parrain = db.query(Parrain).filter(Parrain.id_parrain == parrain_id).first()
    if not parrain:
        raise HTTPException(status_code=404, detail="Parrain non trouvé")

    def vcard_escape(value: str) -> str:
        return (
            value.replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", "\\n")
            .replace("\r", "")
        )

    nom = vcard_escape(parrain.nom or "")
    prenom = vcard_escape(parrain.prenom or "")
    full_name = vcard_escape(" ".join(part for part in [parrain.prenom, parrain.nom] if part))

    lines = ["BEGIN:VCARD", "VERSION:3.0"]
    lines.append(f"N:{nom};{prenom};;;")
    if full_name:
        lines.append(f"FN:{full_name}")
    if parrain.email:
        lines.append(f"EMAIL;TYPE=INTERNET:{vcard_escape(parrain.email)}")
    if parrain.telephone:
        lines.append(f"TEL;TYPE=CELL:{vcard_escape(parrain.telephone)}")
    if parrain.adresse:
        lines.append(f"ADR;TYPE=HOME:;;{vcard_escape(parrain.adresse)};;;;")
    lines.append("END:VCARD")

    content = "\r\n".join(lines) + "\r\n"
    filename = f"parrain_{parrain.id_parrain}.vcf"

    return Response(
        content,
        media_type="text/vcard; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/html/{parrain_id}")
def detail_parrain_html(parrain_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Affiche le détail d'un parrain (HTML)
    """
    if not request.state.user:
        return RedirectResponse("/auth/login")

    parrain = (
        db.query(Parrain)
        .options(joinedload(Parrain.parrainages).joinedload(Parrainage.filleule))
        .filter(Parrain.id_parrain == parrain_id)
        .first()
    )
    if not parrain:
        raise HTTPException(status_code=404, detail="Parrain non trouvé")

    def parrainage_sort_key(item: Parrainage) -> tuple[date, int]:
        ref_date = item.date_fin or item.date_debut or date.min
        return (ref_date, item.id_parrainage or 0)

    ordered = sorted(parrain.parrainages, key=parrainage_sort_key, reverse=True)
    seen = set()
    filleules = []
    for parrainage in ordered:
        filleule = parrainage.filleule
        if not filleule or filleule.id_filleule in seen:
            continue
        seen.add(filleule.id_filleule)
        filleules.append({"filleule": filleule, "parrainage": parrainage})

    return templates.TemplateResponse(
        "parrains/detail.html",
        {"request": request, "parrain": parrain, "filleules": filleules}
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

    remove_parrain_assets(parrain)
    db.query(Parrainage).filter(Parrainage.id_parrain == parrain_id).delete(synchronize_session=False)
    db.delete(parrain)
    db.commit()
    return {"message": "Parrain supprimé"}
