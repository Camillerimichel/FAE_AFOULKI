#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT/uvicorn.pid"
LOG_FILE="$ROOT/uvicorn_fae.log"
VENV_BIN="$ROOT/venv/bin"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8200}"

# Charger .env si présent pour peupler l'environnement
if [[ -f "$ROOT/.env" ]]; then
    set -a
    # shellcheck disable=SC1090
    . "$ROOT/.env"
    set +a
fi

start() {
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "uvicorn déjà démarré (pid $(cat "$PID_FILE"))."
        return 0
    fi

    if [[ ! -x "$VENV_BIN/python" ]]; then
        echo "Venv manquante : $VENV_BIN/python introuvable." >&2
        exit 1
    fi

    echo "Démarrage uvicorn sur $HOST:$PORT..."
    nohup env \
        DB_HOST="${DB_HOST:-127.0.0.1}" \
        DB_PORT="${DB_PORT:-3306}" \
        DB_USER="${DB_USER:-fae_user}" \
        DB_NAME="${DB_NAME:-fae_afoulki}" \
        DB_PASS="${DB_PASS:-change_me}" \
        HOST="$HOST" PORT="$PORT" \
        "$VENV_BIN/python" -m uvicorn app.main:app --host "$HOST" --port "$PORT" --log-level info \
        >> "$LOG_FILE" 2>&1 &

    echo $! > "$PID_FILE"
    echo "uvicorn démarré (pid $(cat "$PID_FILE")). Logs: $LOG_FILE"
}

stop() {
    if [[ ! -f "$PID_FILE" ]]; then
        echo "Pas de pid file. Aucun uvicorn à arrêter ?"
        return 0
    fi
    local pid
    pid="$(cat "$PID_FILE")"
    if kill -0 "$pid" 2>/dev/null; then
        echo "Arrêt uvicorn (pid $pid)..."
        kill "$pid" || true
    else
        echo "Process uvicorn déjà arrêté (pid $pid introuvable)."
    fi
    rm -f "$PID_FILE"
}

status() {
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "uvicorn actif (pid $(cat "$PID_FILE")) sur $HOST:$PORT. Logs: $LOG_FILE"
    else
        echo "uvicorn arrêté."
    fi
}

tail_logs() {
    if [[ -f "$LOG_FILE" ]]; then
        tail -f "$LOG_FILE"
    else
        echo "Pas de log pour le moment ($LOG_FILE absent)."
    fi
}

case "${1:-}" in
    start) start ;;
    stop) stop ;;
    restart) stop; start ;;
    status) status ;;
    tail) tail_logs ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|tail}" >&2
        exit 1
        ;;
esac
