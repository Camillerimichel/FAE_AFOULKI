from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.stats_service import get_dashboard_stats, get_chart_data

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/")
async def admin_index(request: Request):
    if not request.state.user:
        return RedirectResponse("/auth/login")
    return RedirectResponse("/admin/dashboard")


@router.get("/dashboard")
async def admin_dashboard(request: Request):
    if not request.state.user:
        return RedirectResponse("/auth/login")

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
