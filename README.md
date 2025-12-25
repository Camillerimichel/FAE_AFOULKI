FAE Afoulki (FastAPI)
======================

Lancer l'API avec uvicorn et gérer les dépendances.

Pré-requis
- Python 3.12+ conseillé.
- MySQL/MariaDB avec la base `fae_afoulki` accessible (voir `app/database.py`).

Installation
```bash
make install
```
Crée un environnement virtuel `.venv` et installe `requirements.txt`.

Démarrage développement (reload)
```bash
make dev
```

Démarrage production (sans reload)
```bash
make run
```

Notes
- Les fichiers uploadés vont dans `uploads/` (ignoré par git).
- Copie `.env.example` vers `.env` et remplis tes identifiants DB avant de lancer (utilise `DB_HOST=127.0.0.1` et `DB_PORT=3306` si la DB tourne localement).

VS Code (uvicorn)
- Tâches déjà configurées : palette `Run Task` → `uvicorn: start (8200)` / `stop` / `restart` / `tail logs`. Elles appellent `scripts/uvicorn_ctl.sh`.
- Le script `scripts/uvicorn_ctl.sh` gère start/stop/restart/status/tail avec log `uvicorn_fae.log` et pid `uvicorn.pid`. Variables `HOST`/`PORT` surchargées possibles.
