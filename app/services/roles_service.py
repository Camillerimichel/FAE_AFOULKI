from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.role import Role, UserRole
from app.models.user import User

DEFAULT_ROLES = [
    {"name": "administrateur", "label": "Administrateur"},
    {"name": "responsable_fae", "label": "Responsable du FAE"},
    {"name": "back_office_fae", "label": "Back office du FAE"},
    {"name": "parrain", "label": "Parrain"},
    {"name": "correspondant", "label": "Référent"},
    {"name": "filleule", "label": "Filleule"},
]


def ensure_default_roles():
    db: Session = SessionLocal()
    try:
        existing = {role.name for role in db.query(Role).all()}
        for role_data in DEFAULT_ROLES:
            if role_data["name"] not in existing:
                db.add(Role(**role_data))

        db.commit()

        admin_role = db.query(Role).filter(Role.name == "administrateur").first()
        if not admin_role:
            return

        has_assignments = db.query(UserRole).first()
        if has_assignments:
            return

        first_user = db.query(User).order_by(User.id).first()
        if first_user:
            first_user.roles.append(admin_role)
            db.commit()
    finally:
        db.close()
