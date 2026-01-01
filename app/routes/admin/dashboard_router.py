from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.authz import DASHBOARD_ROLES, has_any_role
from app.services.stats_service import get_dashboard_stats, get_chart_data

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def admin_index(request: Request):
    if not request.state.user:
        return RedirectResponse("/auth/login")
    if not has_any_role(request, DASHBOARD_ROLES):
        raise HTTPException(403, "Acces interdit")
    return RedirectResponse("/admin/dashboard")


@router.get("/dashboard")
async def admin_dashboard(request: Request):
    if not request.state.user:
        return RedirectResponse("/auth/login")
    if not has_any_role(request, DASHBOARD_ROLES):
        raise HTTPException(403, "Acces interdit")

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
