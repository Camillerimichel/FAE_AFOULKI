from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.authz import ADMIN_ROLES, has_any_role
from app.services.stats_service import get_dashboard_stats, get_chart_data

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
async def admin_dashboard(request: Request):
    if not request.state.user:
        return RedirectResponse("/auth/login")
    if not has_any_role(request, ADMIN_ROLES):
        raise HTTPException(403, "Accès refusé")

    stats = await get_dashboard_stats()
    charts = await get_chart_data()

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "stats": stats,
            "charts": charts
        }
    )
