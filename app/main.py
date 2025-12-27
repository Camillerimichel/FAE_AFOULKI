from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Base SQLAlchemy + création des tables
from app.database import Base, engine
from app.models.localite import Localite  # noqa: F401

# Middleware session
from app.middleware.session import SessionMiddleware

# Routers
from app.routes.home import router as home_router
from app.routes.filleules import router as filleules_router
from app.routes.parrains import router as parrains_router
from app.routes.parrainages import router as parrainages_router
from app.routes.etablissements import router as etablissements_router
from app.routes.scolarite import router as scolarite_router
from app.routes.correspondants import router as correspondants_router
from app.routes.typesdocuments import router as typesdocuments_router
from app.routes.documents import router as documents_router
from app.routes.suivisocial import router as suivisocial_router
from app.routes.auth_html import router as auth_html_router

from app.routes.admin.dashboard_router import router as dashboard_router
from app.routes.admin.dashboard_api_router import router as dashboard_api_router
from app.routes.admin.export_excel_router import router as export_excel_router
from app.routes.admin.admin_router import router as admin_router
from app.services.roles_service import ensure_default_roles
from app.services.annees_scolaires_service import ensure_annees_scolaires_seed
from app.services.localites_service import (
    ensure_filleule_ville_mapping,
    ensure_localites_seed,
)
from app.services.schema_service import (
    ensure_filleule_photo_column,
    ensure_filleule_etablissement_column,
    ensure_parrain_photo_column,
    ensure_etablissement_type_enum,
    ensure_scolarite_annee_scolaire_column,
    ensure_document_annee_scolaire_column,
    ensure_filleule_correspondant_column,
    ensure_user_password_reset_columns,
)


# --------------------------------------------------
#     INITIALISATION DE L'APPLICATION FASTAPI
# --------------------------------------------------

app = FastAPI(title="FAE Afoulki")

# Ajouter middleware session
app.add_middleware(SessionMiddleware)

# Créer les tables SQLAlchemy si non existantes
Base.metadata.create_all(bind=engine)
ensure_default_roles()
ensure_filleule_photo_column()
ensure_filleule_etablissement_column()
ensure_parrain_photo_column()
ensure_etablissement_type_enum()
ensure_annees_scolaires_seed()
ensure_localites_seed()
ensure_filleule_ville_mapping()
ensure_scolarite_annee_scolaire_column()
ensure_document_annee_scolaire_column()
ensure_filleule_correspondant_column()
ensure_user_password_reset_columns()


# --------------------------------------------------
#     ROUTERS
# --------------------------------------------------

# Admin
app.include_router(admin_router)

# Dashboard admin
app.include_router(dashboard_router)
app.include_router(dashboard_api_router)

# Export Excel
app.include_router(export_excel_router)

# Routers application
app.include_router(home_router)
app.include_router(auth_html_router)
app.include_router(filleules_router)
app.include_router(parrains_router)
app.include_router(parrainages_router)
app.include_router(etablissements_router)
app.include_router(scolarite_router)
app.include_router(correspondants_router)
app.include_router(typesdocuments_router)
app.include_router(documents_router)
app.include_router(suivisocial_router)


# --------------------------------------------------
#     STATIC FILES
# --------------------------------------------------

STATIC_DIR = Path(__file__).resolve().parent / "static"
DOCUMENTS_DIR = Path(__file__).resolve().parent.parent / "Documents"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/Documents", StaticFiles(directory=DOCUMENTS_DIR), name="documents")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(STATIC_DIR / "favicon.png", media_type="image/png")


@app.get("/apple-touch-icon.png", include_in_schema=False)
def apple_touch_icon():
    return FileResponse(STATIC_DIR / "apple-touch-icon.png", media_type="image/png")


@app.get("/apple-touch-icon-precomposed.png", include_in_schema=False)
def apple_touch_icon_precomposed():
    return FileResponse(STATIC_DIR / "apple-touch-icon-precomposed.png", media_type="image/png")
