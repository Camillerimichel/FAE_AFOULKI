from fastapi import APIRouter

from app.routes.admin.admin_filleules import router as admin_filleules_router
from app.routes.admin.admin_parrains import router as admin_parrains_router
from app.routes.admin.admin_parrainages import router as admin_parrainages_router
from app.routes.admin.admin_etablissements import router as admin_etablissements_router
from app.routes.admin.admin_localites import router as admin_localites_router
from app.routes.admin.admin_scolarite import router as admin_scolarite_router
from app.routes.admin.admin_annees_scolaires import router as admin_annees_scolaires_router
from app.routes.admin.admin_correspondants import router as admin_correspondants_router
from app.routes.admin.admin_typesdocuments import router as admin_typesdocuments_router
from app.routes.admin.admin_documents import router as admin_documents_router
from app.routes.admin.admin_suivisocial import router as admin_suivisocial_router
from app.routes.admin.admin_users import router as admin_users_router
from app.routes.admin.admin_connexions import router as admin_connexions_router

router = APIRouter(prefix="/admin", tags=["Admin"])

router.include_router(admin_filleules_router)
router.include_router(admin_parrains_router)
router.include_router(admin_parrainages_router)
router.include_router(admin_etablissements_router)
router.include_router(admin_localites_router)
router.include_router(admin_scolarite_router)
router.include_router(admin_annees_scolaires_router)
router.include_router(admin_correspondants_router)
router.include_router(admin_typesdocuments_router)
router.include_router(admin_documents_router)
router.include_router(admin_suivisocial_router)
router.include_router(admin_users_router)
router.include_router(admin_connexions_router)
