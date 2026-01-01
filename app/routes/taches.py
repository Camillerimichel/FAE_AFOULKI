from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import case
from sqlalchemy.orm import Session, selectinload

from app.authz import has_any_role
from app.database import get_db
from app.models.correspondant import Correspondant
from app.models.filleule import Filleule
from app.models.parrain import Parrain
from app.models.tache import (
    TASK_STATUSES,
    TASK_TARGETS,
    TaskComment,
    Tache,
    TacheObjet,
)
from app.models.user import User
from app.schemas.tache import TacheCommentCreate, TacheCreate, TacheResponse, TacheUpdate

router = APIRouter(prefix="/taches", tags=["Tâches"])
templates = Jinja2Templates(directory="app/templates")

MANAGE_ROLES = {"correspondant", "back_office_fae", "responsable_fae", "administrateur", "membre"}

TASK_OBJECT_LABELS = {
    "demande_info": "Demande d'information",
    "demande_document": "Demande de document",
    "demande_entretien": "Demande d'entretien",
    "demande_aide_sociale": "Demande d'aide sociale",
    "preparation_remise_bourses": "Preparation des remises des bourses",
    "attribution_bourses": "Attribution des bourses",
    "relance_dons": "Relance des dons",
    "envoi_email": "Envoi d'email",
    "autre": "Autre",
}

TASK_STATUS_LABELS = {
    "A faire": "A faire",
    "En cours": "En cours",
    "En attente": "En attente",
    "Realise": "Realise",
}

TASK_TARGET_LABELS = {
    "filleule": "Filleule",
    "correspondant": "Referent",
    "parrain": "Parrain",
    "backoffice": "Back office",
    "fae": "FAE",
    "autre": "Autre",
}

STATUS_BADGES = {
    "A faire": "bg-amber-100 text-amber-700",
    "En cours": "bg-sky-100 text-sky-700",
    "En attente": "bg-purple-100 text-purple-700",
    "Realise": "bg-emerald-100 text-emerald-700",
}


def require_login(request: Request):
    if not request.state.user:
        return False
    return True


def can_manage_tasks(request: Request) -> bool:
    return has_any_role(request, MANAGE_ROLES)


def is_assigned(task: Tache, user: User | None) -> bool:
    if not user:
        return False
    return any(assignee.id == user.id for assignee in task.assignees)


def format_user_label(user: User) -> str:
    if user.fullname:
        return user.fullname
    if user.email:
        return user.email
    return f"Utilisateur {user.id}"


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return date.fromisoformat(cleaned)
    except ValueError as exc:
        raise HTTPException(400, "Date invalide") from exc


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    try:
        return int(cleaned)
    except ValueError as exc:
        raise HTTPException(400, "Valeur invalide") from exc


def fetch_task_objects(db: Session) -> list[TacheObjet]:
    return (
        db.query(TacheObjet)
        .order_by(case((TacheObjet.code == "autre", 1), else_=0), TacheObjet.code)
        .all()
    )


def get_task_object(db: Session, objet_id: int) -> TacheObjet:
    task_objet = db.query(TacheObjet).filter(TacheObjet.id_objet == objet_id).first()
    if not task_objet:
        raise HTTPException(400, "Objet invalide")
    return task_objet


def resolve_target_id(
    cible_type: str,
    cible_id_filleule: str | None,
    cible_id_parrain: str | None,
    cible_id_correspondant: str | None,
) -> int | None:
    if cible_type == "filleule":
        return parse_int(cible_id_filleule)
    if cible_type == "parrain":
        return parse_int(cible_id_parrain)
    if cible_type == "correspondant":
        return parse_int(cible_id_correspondant)
    return None


def validate_task_data(statut: str, date_debut: date | None, date_fin: date | None):
    if not date_debut:
        raise HTTPException(400, "La date de debut est obligatoire")
    if statut == "Realise" and not date_fin:
        raise HTTPException(400, "La date de fin est obligatoire quand la tache est realisee")
    if date_fin and date_debut and date_fin < date_debut:
        raise HTTPException(400, "La date de fin doit etre apres la date de debut")


def build_target_labels(tasks: list[Tache], db: Session) -> dict[int, str]:
    filleule_ids = {t.cible_id for t in tasks if t.cible_type == "filleule" and t.cible_id}
    parrain_ids = {t.cible_id for t in tasks if t.cible_type == "parrain" and t.cible_id}
    correspondant_ids = {t.cible_id for t in tasks if t.cible_type == "correspondant" and t.cible_id}

    filleules = {}
    if filleule_ids:
        rows = db.query(Filleule).filter(Filleule.id_filleule.in_(filleule_ids)).all()
        filleules = {row.id_filleule: f"{row.prenom} {row.nom}".strip() for row in rows}

    parrains = {}
    if parrain_ids:
        rows = db.query(Parrain).filter(Parrain.id_parrain.in_(parrain_ids)).all()
        parrains = {row.id_parrain: f"{row.prenom} {row.nom}".strip() for row in rows}

    correspondants = {}
    if correspondant_ids:
        rows = db.query(Correspondant).filter(Correspondant.id_correspondant.in_(correspondant_ids)).all()
        correspondants = {row.id_correspondant: f"{row.prenom} {row.nom}".strip() for row in rows}

    labels: dict[int, str] = {}
    for task in tasks:
        label = "-"
        if task.cible_type == "filleule":
            label = filleules.get(task.cible_id, "-")
        elif task.cible_type == "parrain":
            label = parrains.get(task.cible_id, "-")
        elif task.cible_type == "correspondant":
            label = correspondants.get(task.cible_id, "-")
        else:
            label = TASK_TARGET_LABELS.get(task.cible_type, "-")
        labels[task.id_tache] = label
    return labels


def build_comment_thread(comments: list[TaskComment]) -> str:
    lines = []
    for comment in comments:
        author = "Utilisateur"
        if comment.author:
            author = format_user_label(comment.author)
        stamp = comment.created_at.strftime("%Y-%m-%d %H:%M") if comment.created_at else "-"
        lines.append(f"[{stamp}] {author}: {comment.content}")
    return "\n".join(lines)


@router.get("/")
def taches_list_html(request: Request, db: Session = Depends(get_db)):
    if not require_login(request):
        return RedirectResponse("/auth/login")

    manage = can_manage_tasks(request)
    query = (
        db.query(Tache)
        .options(
            selectinload(Tache.assignees),
            selectinload(Tache.created_by),
            selectinload(Tache.objet),
        )
        .order_by(Tache.date_debut.desc(), Tache.id_tache.desc())
    )
    if not manage:
        query = query.join(Tache.assignees).filter(User.id == request.state.user.id)

    tasks = query.all()
    target_labels = build_target_labels(tasks, db)
    assignees_display = {
        task.id_tache: ", ".join(format_user_label(user) for user in task.assignees) or "-"
        for task in tasks
    }
    status_counts = {status: 0 for status in TASK_STATUSES}
    for task in tasks:
        status_counts[task.statut] = status_counts.get(task.statut, 0) + 1

    return templates.TemplateResponse(
        "taches/list.html",
        {
            "request": request,
            "tasks": tasks,
            "can_manage": manage,
            "object_labels": TASK_OBJECT_LABELS,
            "status_labels": TASK_STATUS_LABELS,
            "status_badges": STATUS_BADGES,
            "target_labels": target_labels,
            "assignees_display": assignees_display,
            "status_counts": status_counts,
            "statuses": TASK_STATUSES,
        },
    )


@router.get("/pdf")
def taches_pdf(request: Request, db: Session = Depends(get_db)):
    if not require_login(request):
        return RedirectResponse("/auth/login")

    open_statuses = [status for status in TASK_STATUSES if status != "Realise"]
    tasks = (
        db.query(Tache)
        .options(
            selectinload(Tache.assignees),
            selectinload(Tache.comments).selectinload(TaskComment.author),
            selectinload(Tache.objet),
        )
        .filter(Tache.statut.in_(open_statuses))
        .order_by(Tache.statut, Tache.date_debut, Tache.id_tache)
        .all()
    )

    target_labels = build_target_labels(tasks, db)
    grouped = []
    for status in open_statuses:
        status_tasks = [task for task in tasks if task.statut == status]
        if not status_tasks:
            continue
        date_groups: dict[date | None, list[Tache]] = {}
        for task in status_tasks:
            date_groups.setdefault(task.date_debut, []).append(task)
        ordered_dates = sorted(
            date_groups.items(),
            key=lambda item: (item[0] is None, item[0] or date.min),
        )
        date_sections = []
        for date_value, items in ordered_dates:
            date_label = date_value.strftime("%d/%m/%Y") if date_value else "-"
            rows = []
            for task in items:
                assignees_label = ", ".join(format_user_label(user) for user in task.assignees) or "-"
                rows.append(
                    {
                        "task": task,
                        "target_label": target_labels.get(task.id_tache, "-"),
                        "assignees_label": assignees_label,
                        "comment_thread": build_comment_thread(task.comments),
                    }
                )
            date_sections.append({"date_label": date_label, "tasks": rows})
        grouped.append(
            {
                "status": status,
                "status_label": TASK_STATUS_LABELS.get(status, status),
                "date_sections": date_sections,
            }
        )

    return templates.TemplateResponse(
        "taches/pdf.html",
        {
            "request": request,
            "groups": grouped,
            "object_labels": TASK_OBJECT_LABELS,
            "today_label": datetime.now().strftime("%d/%m/%Y"),
        },
    )


@router.get("/new")
def tache_new_form(request: Request, db: Session = Depends(get_db)):
    if not require_login(request):
        return RedirectResponse("/auth/login")
    if not can_manage_tasks(request):
        raise HTTPException(403, "Acces interdit")

    users = db.query(User).order_by(User.fullname.is_(None), User.fullname).all()
    filleules = db.query(Filleule).order_by(Filleule.nom, Filleule.prenom).all()
    parrains = db.query(Parrain).order_by(Parrain.nom, Parrain.prenom).all()
    correspondants = db.query(Correspondant).order_by(Correspondant.nom, Correspondant.prenom).all()
    objects = fetch_task_objects(db)
    return templates.TemplateResponse(
        "taches/form.html",
        {
            "request": request,
            "action": "Creer",
            "task": None,
            "object_labels": TASK_OBJECT_LABELS,
            "status_labels": TASK_STATUS_LABELS,
            "target_labels": TASK_TARGET_LABELS,
            "statuses": TASK_STATUSES,
            "objects": objects,
            "targets": TASK_TARGETS,
            "users": users,
            "assigned_ids": [],
            "filleules": filleules,
            "parrains": parrains,
            "correspondants": correspondants,
        },
    )


@router.post("/new")
def tache_create(
    request: Request,
    titre: str = Form(...),
    objet_id: str = Form(...),
    statut: str = Form(...),
    date_debut: str = Form(...),
    date_fin: str = Form(None),
    description: str = Form(None),
    cible_type: str = Form(None),
    cible_id_filleule: str = Form(None),
    cible_id_parrain: str = Form(None),
    cible_id_correspondant: str = Form(None),
    assignees: list[str] = Form([]),
    db: Session = Depends(get_db),
):
    if not require_login(request):
        return RedirectResponse("/auth/login")
    if not can_manage_tasks(request):
        raise HTTPException(403, "Acces interdit")

    objet_id_val = parse_int(objet_id)
    if objet_id_val is None:
        raise HTTPException(400, "Objet invalide")
    task_objet = get_task_object(db, objet_id_val)

    if statut not in TASK_STATUSES:
        raise HTTPException(400, "Statut invalide")

    cible_type_value = (cible_type or "").strip() or "autre"
    if cible_type_value not in TASK_TARGETS:
        raise HTTPException(400, "Cible invalide")

    date_debut_val = parse_date(date_debut)
    date_fin_val = parse_date(date_fin)
    validate_task_data(statut, date_debut_val, date_fin_val)

    cible_id = resolve_target_id(
        cible_type_value,
        cible_id_filleule,
        cible_id_parrain,
        cible_id_correspondant,
    )
    if cible_type_value in {"filleule", "parrain", "correspondant"} and not cible_id:
        raise HTTPException(400, "La cible selectionnee est obligatoire")

    assignee_ids = []
    for value in assignees:
        assignee_ids.append(parse_int(value))
    assignee_ids = [value for value in assignee_ids if value is not None]

    assignee_users = []
    if assignee_ids:
        assignee_users = db.query(User).filter(User.id.in_(assignee_ids)).all()

    task = Tache(
        titre=titre.strip(),
        description=description.strip() if description else None,
        objet_id=task_objet.id_objet,
        statut=statut,
        date_debut=date_debut_val,
        date_fin=date_fin_val if statut == "Realise" else None,
        cible_type=cible_type_value,
        cible_id=cible_id,
        created_by_id=request.state.user.id,
    )
    task.assignees = assignee_users

    db.add(task)
    db.commit()

    return RedirectResponse(f"/taches/{task.id_tache}", status_code=302)


@router.get("/{tache_id}")
def tache_detail(tache_id: int, request: Request, db: Session = Depends(get_db)):
    if not require_login(request):
        return RedirectResponse("/auth/login")

    task = (
        db.query(Tache)
        .options(
            selectinload(Tache.assignees),
            selectinload(Tache.created_by),
            selectinload(Tache.comments).selectinload(TaskComment.author),
            selectinload(Tache.objet),
        )
        .filter(Tache.id_tache == tache_id)
        .first()
    )
    if not task:
        raise HTTPException(404, "Tache introuvable")

    manage = can_manage_tasks(request)
    if not manage and not is_assigned(task, request.state.user):
        raise HTTPException(403, "Acces interdit")

    target_labels = build_target_labels([task], db)
    assignees_display = ", ".join(format_user_label(user) for user in task.assignees) or "-"
    comment_thread = build_comment_thread(task.comments)
    can_comment = manage or is_assigned(task, request.state.user)

    return templates.TemplateResponse(
        "taches/detail.html",
        {
            "request": request,
            "task": task,
            "target_label": target_labels.get(task.id_tache, "-"),
            "assignees_display": assignees_display,
            "object_labels": TASK_OBJECT_LABELS,
            "status_labels": TASK_STATUS_LABELS,
            "status_badges": STATUS_BADGES,
            "comment_thread": comment_thread,
            "can_manage": manage,
            "can_comment": can_comment,
        },
    )


@router.get("/{tache_id}/edit")
def tache_edit_form(tache_id: int, request: Request, db: Session = Depends(get_db)):
    if not require_login(request):
        return RedirectResponse("/auth/login")
    if not can_manage_tasks(request):
        raise HTTPException(403, "Acces interdit")

    task = (
        db.query(Tache)
        .options(
            selectinload(Tache.assignees),
            selectinload(Tache.comments).selectinload(TaskComment.author),
            selectinload(Tache.objet),
        )
        .filter(Tache.id_tache == tache_id)
        .first()
    )
    if not task:
        raise HTTPException(404, "Tache introuvable")

    users = db.query(User).order_by(User.fullname.is_(None), User.fullname).all()
    filleules = db.query(Filleule).order_by(Filleule.nom, Filleule.prenom).all()
    parrains = db.query(Parrain).order_by(Parrain.nom, Parrain.prenom).all()
    correspondants = db.query(Correspondant).order_by(Correspondant.nom, Correspondant.prenom).all()
    objects = fetch_task_objects(db)

    return templates.TemplateResponse(
        "taches/form.html",
        {
            "request": request,
            "action": "Modifier",
            "task": task,
            "object_labels": TASK_OBJECT_LABELS,
            "status_labels": TASK_STATUS_LABELS,
            "target_labels": TASK_TARGET_LABELS,
            "statuses": TASK_STATUSES,
            "objects": objects,
            "targets": TASK_TARGETS,
            "users": users,
            "assigned_ids": [user.id for user in task.assignees],
            "filleules": filleules,
            "parrains": parrains,
            "correspondants": correspondants,
            "comment_thread": build_comment_thread(task.comments),
            "can_comment": True,
        },
    )


@router.post("/{tache_id}/edit")
def tache_update(
    tache_id: int,
    request: Request,
    titre: str = Form(...),
    objet_id: str = Form(...),
    statut: str = Form(...),
    date_debut: str = Form(...),
    date_fin: str = Form(None),
    description: str = Form(None),
    cible_type: str = Form(None),
    cible_id_filleule: str = Form(None),
    cible_id_parrain: str = Form(None),
    cible_id_correspondant: str = Form(None),
    assignees: list[str] = Form([]),
    db: Session = Depends(get_db),
):
    if not require_login(request):
        return RedirectResponse("/auth/login")
    if not can_manage_tasks(request):
        raise HTTPException(403, "Acces interdit")

    task = (
        db.query(Tache)
        .options(selectinload(Tache.assignees))
        .filter(Tache.id_tache == tache_id)
        .first()
    )
    if not task:
        raise HTTPException(404, "Tache introuvable")

    objet_id_val = parse_int(objet_id)
    if objet_id_val is None:
        raise HTTPException(400, "Objet invalide")
    task_objet = get_task_object(db, objet_id_val)

    if statut not in TASK_STATUSES:
        raise HTTPException(400, "Statut invalide")
    cible_type_value = (cible_type or "").strip() or "autre"
    if cible_type_value not in TASK_TARGETS:
        raise HTTPException(400, "Cible invalide")

    date_debut_val = parse_date(date_debut)
    date_fin_val = parse_date(date_fin)
    validate_task_data(statut, date_debut_val, date_fin_val)

    cible_id = resolve_target_id(
        cible_type_value,
        cible_id_filleule,
        cible_id_parrain,
        cible_id_correspondant,
    )

    assignee_ids = []
    for value in assignees:
        assignee_ids.append(parse_int(value))
    assignee_ids = [value for value in assignee_ids if value is not None]

    assignee_users = []
    if assignee_ids:
        assignee_users = db.query(User).filter(User.id.in_(assignee_ids)).all()

    task.statut = statut
    task.objet_id = task_objet.id_objet
    task.date_fin = date_fin_val if statut == "Realise" else None
    task.assignees = assignee_users

    db.commit()

    return RedirectResponse(f"/taches/{task.id_tache}", status_code=302)


@router.post("/{tache_id}/comment")
def tache_add_comment(
    tache_id: int,
    request: Request,
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    if not require_login(request):
        return RedirectResponse("/auth/login")

    task = (
        db.query(Tache)
        .options(selectinload(Tache.assignees))
        .filter(Tache.id_tache == tache_id)
        .first()
    )
    if not task:
        raise HTTPException(404, "Tache introuvable")

    manage = can_manage_tasks(request)
    if not manage and not is_assigned(task, request.state.user):
        raise HTTPException(403, "Acces interdit")

    note = content.strip()
    if not note:
        raise HTTPException(400, "Commentaire vide")

    comment = TaskComment(
        task_id=task.id_tache,
        author_id=request.state.user.id,
        content=note,
    )
    db.add(comment)
    db.commit()

    return RedirectResponse(f"/taches/{task.id_tache}", status_code=302)


# --------------------------------------------------------
#                      API CRUD JSON
# --------------------------------------------------------

@router.get("/api", response_model=list[TacheResponse])
def get_taches(db: Session = Depends(get_db)):
    return db.query(Tache).options(selectinload(Tache.assignees)).all()


@router.get("/api/{tache_id}", response_model=TacheResponse)
def get_tache(tache_id: int, db: Session = Depends(get_db)):
    task = db.query(Tache).options(selectinload(Tache.assignees)).filter(Tache.id_tache == tache_id).first()
    if not task:
        raise HTTPException(404, "Tache introuvable")
    return task


@router.post("/api", response_model=TacheResponse)
def create_tache(data: TacheCreate, db: Session = Depends(get_db)):
    task_objet = get_task_object(db, data.objet_id)
    if data.statut not in TASK_STATUSES:
        raise HTTPException(400, "Statut invalide")
    if data.cible_type not in TASK_TARGETS:
        raise HTTPException(400, "Cible invalide")

    validate_task_data(data.statut, data.date_debut, data.date_fin)
    if data.cible_type in {"filleule", "parrain", "correspondant"} and not data.cible_id:
        raise HTTPException(400, "La cible selectionnee est obligatoire")

    assignee_users = []
    if data.assignee_ids:
        assignee_users = db.query(User).filter(User.id.in_(data.assignee_ids)).all()

    task = Tache(
        titre=data.titre.strip(),
        description=data.description.strip() if data.description else None,
        objet_id=task_objet.id_objet,
        statut=data.statut,
        date_debut=data.date_debut,
        date_fin=data.date_fin if data.statut == "Realise" else None,
        cible_type=data.cible_type,
        cible_id=data.cible_id,
    )
    task.assignees = assignee_users

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/api/{tache_id}", response_model=TacheResponse)
def update_tache(tache_id: int, data: TacheUpdate, db: Session = Depends(get_db)):
    task = db.query(Tache).options(selectinload(Tache.assignees)).filter(Tache.id_tache == tache_id).first()
    if not task:
        raise HTTPException(404, "Tache introuvable")

    task_objet = get_task_object(db, data.objet_id)
    if data.statut not in TASK_STATUSES:
        raise HTTPException(400, "Statut invalide")
    if data.cible_type not in TASK_TARGETS:
        raise HTTPException(400, "Cible invalide")

    validate_task_data(data.statut, data.date_debut, data.date_fin)
    if data.cible_type in {"filleule", "parrain", "correspondant"} and not data.cible_id:
        raise HTTPException(400, "La cible selectionnee est obligatoire")

    assignee_users = []
    if data.assignee_ids:
        assignee_users = db.query(User).filter(User.id.in_(data.assignee_ids)).all()

    task.titre = data.titre.strip()
    task.objet_id = task_objet.id_objet
    task.statut = data.statut
    task.date_debut = data.date_debut
    task.date_fin = data.date_fin if data.statut == "Realise" else None
    task.cible_type = data.cible_type
    task.cible_id = data.cible_id
    task.assignees = assignee_users

    db.commit()
    db.refresh(task)
    return task


@router.post("/api/{tache_id}/comments")
def add_tache_comment(tache_id: int, data: TacheCommentCreate, db: Session = Depends(get_db)):
    task = db.query(Tache).filter(Tache.id_tache == tache_id).first()
    if not task:
        raise HTTPException(404, "Tache introuvable")

    note = data.content.strip()
    if not note:
        raise HTTPException(400, "Commentaire vide")

    comment = TaskComment(task_id=task.id_tache, author_id=data.author_id, content=note)
    db.add(comment)
    db.commit()

    return {"message": "Commentaire ajoute"}
