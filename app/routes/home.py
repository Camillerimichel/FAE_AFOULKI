import json

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.services.stats_service import (
    get_chart_data,
    get_city_origin_stats,
    get_dashboard_stats,
    get_filiere_stats,
    get_essaouira_map,
    get_annees_scolaires,
)

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()

@router.get("/", tags=["Home"])
async def dashboard(request: Request):
    stats = {
        "filleules": 0,
        "parrains": 0,
        "parrainages": 0,
        "documents": 0,
        "annees_scolaires": 0,
        "couverture_sante": 0,
    }
    charts = {
        "filleuls_par_etab": [],
        "parrainages_par_annee": [],
        "etablissements": [],
        "annees": [],
        "niveaux_labels": [],
        "niveaux_data": [],
    }
    city_stats = {"cities": [], "missing": []}
    filiere_stats = []
    annees_scolaires = []
    map_data = None
    if request.state.user:
        stats = await get_dashboard_stats()
        charts = await get_chart_data()
        city_stats = await get_city_origin_stats()
        filiere_stats = await get_filiere_stats()
        annees_scolaires = await get_annees_scolaires()
        map_data = get_essaouira_map()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "charts": charts,
            "city_stats": city_stats,
            "filiere_stats": filiere_stats,
            "annees_scolaires": annees_scolaires,
            "map_json": json.dumps(map_data) if map_data else "null",
            "city_json": json.dumps(city_stats["cities"]),
        },
    )
