from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.authz import ADMIN_ROLES, has_any_role
from app.database import get_db
from app.models.scolarite import Scolarite
from app.models.filleule import Filleule
from app.models.etablissement import Etablissement
from app.models.annee_scolaire import AnneeScolaire

router = APIRouter(prefix="/scolarite", tags=["Admin - Scolarité"])
templates = Jinja2Templates(directory="app/templates")


# --- Vérification session ---
def check_session(request: Request):
    if not request.state.user:
        return False
    if not has_any_role(request, ADMIN_ROLES):
        raise HTTPException(403, "Accès refusé")
    return True


# --- LISTE ---
@router.get("/")
def admin_scolarite_list(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    liste = db.query(Scolarite).all()

    return templates.TemplateResponse(
        "admin/scolarite/list.html",
        {"request": request, "scolarites": liste},
    )


# --- CREER ---
@router.get("/new")
def admin_scolarite_new(request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    filleules = db.query(Filleule).all()
    etablissements = db.query(Etablissement).all()
    annees = db.query(AnneeScolaire).order_by(AnneeScolaire.periode).all()

    return templates.TemplateResponse(
        "admin/scolarite/form.html",
        {
            "request": request,
            "action": "Créer",
            "scolarite": None,
            "filleules": filleules,
            "etablissements": etablissements,
            "annees": annees,
            "selected_annee_id": None,
        },
    )


@router.post("/new")
def admin_scolarite_create(
    request: Request,
    id_filleule: int = Form(...),
    id_etablissement: int = Form(...),
    id_annee_scolaire: int = Form(...),
    niveau: str = Form(...),
    resultats: str = Form(...),
    diplome_obtenu: str = Form(...),
    db: Session = Depends(get_db),
):
    annee = (
        db.query(AnneeScolaire)
        .filter(AnneeScolaire.id_annee_scolaire == id_annee_scolaire)
        .first()
    )
    if not annee:
        raise HTTPException(400, "Année scolaire invalide")

    s = Scolarite(
        id_filleule=id_filleule,
        id_etablissement=id_etablissement,
        id_annee_scolaire=id_annee_scolaire,
        annee_scolaire=annee.periode,
        niveau=niveau,
        resultats=resultats,
        diplome_obtenu=diplome_obtenu,
    )

    db.add(s)
    db.commit()

    return RedirectResponse("/admin/scolarite", status_code=302)


# --- DETAIL ---
@router.get("/{id_scolarite}")
def admin_scolarite_detail(id_scolarite: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    s = db.query(Scolarite).filter(Scolarite.id_scolarite == id_scolarite).first()
    if not s:
        raise HTTPException(404, "Enregistrement scolarité non trouvé")

    return templates.TemplateResponse(
        "admin/scolarite/detail.html",
        {"request": request, "scolarite": s},
    )


# --- EDITER ---
@router.get("/{id_scolarite}/edit")
def admin_scolarite_edit(id_scolarite: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    s = db.query(Scolarite).filter(Scolarite.id_scolarite == id_scolarite).first()
    if not s:
        raise HTTPException(404, "Enregistrement scolarité non trouvé")

    filleules = db.query(Filleule).all()
    etablissements = db.query(Etablissement).all()
    annees = db.query(AnneeScolaire).order_by(AnneeScolaire.periode).all()
    selected_annee_id = s.id_annee_scolaire
    if not selected_annee_id and s.annee_scolaire:
        periode = s.annee_scolaire
        matched = (
            db.query(AnneeScolaire)
            .filter(AnneeScolaire.periode == periode)
            .first()
        )
        if not matched and "-" in periode:
            normalized = periode.replace("-", "/")
            matched = (
                db.query(AnneeScolaire)
                .filter(AnneeScolaire.periode == normalized)
                .first()
            )
        if matched:
            selected_annee_id = matched.id_annee_scolaire

    return templates.TemplateResponse(
        "admin/scolarite/form.html",
        {
            "request": request,
            "action": "Modifier",
            "scolarite": s,
            "filleules": filleules,
            "etablissements": etablissements,
            "annees": annees,
            "selected_annee_id": selected_annee_id,
        },
    )


@router.post("/{id_scolarite}/edit")
def admin_scolarite_update(
    id_scolarite: int,
    request: Request,
    id_filleule: int = Form(...),
    id_etablissement: int = Form(...),
    id_annee_scolaire: int = Form(...),
    niveau: str = Form(...),
    resultats: str = Form(...),
    diplome_obtenu: str = Form(...),
    db: Session = Depends(get_db),
):
    s = db.query(Scolarite).filter(Scolarite.id_scolarite == id_scolarite).first()
    if not s:
        raise HTTPException(404, "Enregistrement scolarité non trouvé")

    annee = (
        db.query(AnneeScolaire)
        .filter(AnneeScolaire.id_annee_scolaire == id_annee_scolaire)
        .first()
    )
    if not annee:
        raise HTTPException(400, "Année scolaire invalide")

    s.id_filleule = id_filleule
    s.id_etablissement = id_etablissement
    s.id_annee_scolaire = id_annee_scolaire
    s.annee_scolaire = annee.periode
    s.niveau = niveau
    s.resultats = resultats
    s.diplome_obtenu = diplome_obtenu

    db.commit()

    return RedirectResponse(f"/admin/scolarite/{id_scolarite}", status_code=302)


# --- DELETE ---
@router.get("/{id_scolarite}/delete")
def admin_scolarite_delete(id_scolarite: int, request: Request, db: Session = Depends(get_db)):
    if not check_session(request):
        return RedirectResponse("/auth/login")

    s = db.query(Scolarite).filter(Scolarite.id_scolarite == id_scolarite).first()
    if not s:
        raise HTTPException(404, "Enregistrement scolarité non trouvé")

    db.delete(s)
    db.commit()

    return RedirectResponse("/admin/scolarite", status_code=302)
