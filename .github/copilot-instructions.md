<!-- Instructions concises pour les agents Codex/Copilot travaillant sur ce dépôt -->
# Copilot / Agent instructions — FAE Afoulki (FastAPI)

But: aider un agent à être immédiatement productif sur ce backend FastAPI.

- **Big picture**: l'app est une API FastAPI monolithique avec routers organisés
  par ressource dans `app/routes/` (et routes admin dans `app/routes/admin/`).
  L'app est démarrée depuis `app.main:app`. Le schéma SQLAlchemy est défini
  dans `app/models/` et initialisé par `Base.metadata.create_all(bind=engine)`.

- **Points d'intégration critiques**:
  - DB: `app/database.py` construit `DATABASE_URL` depuis `.env` (vars `DB_USER`,
    `DB_PASS`, `DB_HOST`, `DB_PORT`, `DB_NAME`). Le driver utilisé est `mysql+pymysql`.
  - Sessions: `app/middleware/session.py` lit le cookie `session` et charge
    l'utilisateur via SQLAlchemy; il place `request.state.user` et
    `request.state.user_roles` (ensemble de `role.name`). Le cookie attend un
    identifiant numérique d'utilisateur.
  - Démarrage: `app/main.py` appelle `ensure_default_roles()` et
    `ensure_filleule_photo_column()` (voir `app/services/roles_service.py` et
    `app/services/schema_service.py`). Ne pas supposer qu'un outil de migration
    (alembic) est présent — le projet crée/ajuste le schéma à l'initialisation.

- **Conventions de code et organisation**:
  - Routers: chaque ressource => `app/routes/<resource>.py` expose un `router`.
  - Admin: routes admin regroupées dans `app/routes/admin/` et incluses globalement.
  - Templates: Jinja2 dans `app/templates/`. Static dans `app/static/`.
  - Uploads: fichiers utilisateurs dans `uploads/` et `Documents/` montés par l'app.
  - Services utilitaires: `app/services/*` (ex: role/schema/stats).

- **Workflows développeur (rapide)**:
  - Installer: `make install` (crée `.venv` et installe `requirements.txt`).
  - Dev (reload): `make dev` (uvicorn --reload). Exemple rapide:
    ```bash
    make install
    make dev HOST=127.0.0.1 PORT=8200
    ```
  - Production (sans reload): `make run` ou `bash scripts/uvicorn_ctl.sh start`.
  - Contrôle du service: `bash scripts/uvicorn_ctl.sh {start|stop|restart|status|tail}`
    Logs: `uvicorn_fae.log`, pid dans `uvicorn.pid`.
  - VSCode tasks déjà fournies: `uvicorn: start (8200)` etc (voir README).

- **Conseils pratiques spécifiques**:
  - Si vous modifiez les modèles SQLAlchemy, vérifiez `app/main.py` et
    `app/services/schema_service.py` : l'app n'utilise pas Alembic; certaines
    migrations légères sont implémentées manuellement (ex: ajout de colonne
    `photo` pour `Filleules`).
  - Pour l'auth/session, le middleware lit `session` cookie et fait `int()` —
    protéger les conversions et tester les cookies en dev.
  - Les rôles par défaut sont créés au démarrage (`ensure_default_roles`).
    Tests/ops qui ajoutent un utilisateur doivent considérer l'assignation
    automatique du premier utilisateur comme `administrateur` si aucun rôle
    n'existe.

- **Fichiers à consulter rapidement pour contexte**:
  - `app/main.py` — point d'entrée, inclusion des routers
  - `app/database.py` — connexion DB et variables d'environnement
  - `app/middleware/session.py` — comportement de session / request.state
  - `app/models/` — définitions SQLAlchemy
  - `app/routes/` & `app/routes/admin/` — organisation des endpoints
  - `app/services/roles_service.py` et `app/services/schema_service.py` — logique
    d'initialisation / ajustement du schéma
  - `scripts/uvicorn_ctl.sh`, `Makefile`, `README.md` — workflows d'exécution

- **Réponses attendues d'un agent**:
  - Quand on demande de modifier un modèle: proposer les changements dans
    `app/models/`, expliquer l'impact sur `Base.metadata.create_all` et proposer
    une modification de `app/services/schema_service.py` si une migration
    compatible est nécessaire.
  - Quand on touche auth/session: vérifier `app/middleware/session.py` et les
    endroits qui lisent `request.state.user` ou `request.state.user_roles`.

Si une information manque (ex: fichier `.env.example` absent ou migrations
plus complexes), demandez au mainteneur plutôt que d'assumer un pattern.
