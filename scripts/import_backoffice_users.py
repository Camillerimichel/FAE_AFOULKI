import os
import secrets

from app.database import SessionLocal
from app.models import (  # noqa: F401
    annee_scolaire,
    correspondant,
    document,
    etablissement,
    filleule,
    localite,
    parrain,
    parrainage,
    role,
    scolarite,
    suivisocial,
    typedocument,
    user,
)
from app.models.role import Role
from app.models.user import User
from app.security import hash_password
from app.services.email_service import send_email
from app.services.password_reset_service import set_user_reset_token
from app.services.roles_service import ensure_default_roles
from app.services.schema_service import ensure_user_password_reset_columns


USERS = [
    {"fullname": "FOSSAT Sylvie", "email": "sylvie.fossat33@orange.fr"},
    {"fullname": "Bikerouane khadija", "email": "bikerouane.khadija874@gmail.com"},
    {"fullname": "idrissi mohammed", "email": "mohmmedidrissi3@gmail.com"},
    {"fullname": "LOULOUM Marie Claude", "email": "louloum.marieclaude@free.fr"},
    {"fullname": "veronique hammerer", "email": "vhammerer33@gmail.com"},
    {"fullname": "KORCZENIUK Christophe", "email": "ckorczeniuk@gmail.com"},
    {"fullname": "LARRIEU Josiane", "email": "jojo.larrieu@gmail.com"},
    {"fullname": "Michele Aebi", "email": "michele.aebi@orange.fr"},
    {"fullname": "Patrice Claverie", "email": "patriceclaverie33160@gmail.com"},
    {"fullname": "stephane talavet", "email": "stephane.talavet@gmail.com"},
    {"fullname": "marie watel", "email": "mariechrist.watel@gmail.com"},
]


def main():
    ensure_default_roles()
    ensure_user_password_reset_columns()
    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.name == "back_office_fae").first()
        if not role:
            print("Role back_office_fae introuvable.")
            return

        base_url = os.getenv("APP_BASE_URL", "http://localhost:8000").rstrip("/")
        created = 0
        updated = 0
        emailed = 0
        email_failed = 0

        for entry in USERS:
            email = entry["email"].strip().lower()
            fullname = entry["fullname"].strip()
            user = db.query(User).filter(User.email == email).first()
            is_new = False
            if not user:
                temp_password = secrets.token_urlsafe(16)
                user = User(email=email, fullname=fullname, hashed_password=hash_password(temp_password))
                db.add(user)
                is_new = True
            else:
                if not user.fullname:
                    user.fullname = fullname

            if role not in user.roles:
                user.roles.append(role)

            token = set_user_reset_token(user)
            db.commit()

            reset_link = f"{base_url}/auth/reset-password?token={token}"
            subject = "Acces Back Office FAE - Definir votre mot de passe"
            body = (
                "Bonjour,\n\n"
                "Votre acces Back Office est cree.\n"
                "Cliquez sur le lien ci-dessous pour definir ou modifier votre mot de passe :\n"
                f"{reset_link}\n\n"
                "Si vous n'etes pas a l'origine de cette demande, ignorez cet email.\n"
            )
            ok, err = send_email(email, subject, body)
            if ok:
                emailed += 1
            else:
                email_failed += 1
                print(f"[email] envoi impossible pour {email}: {err}")
                print(f"[email] lien de reinitialisation: {reset_link}")

            if is_new:
                created += 1
            else:
                updated += 1

        print(f"Import termine. Crees: {created}, mis a jour: {updated}.")
        print(f"Emails envoyes: {emailed}, echecs: {email_failed}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
