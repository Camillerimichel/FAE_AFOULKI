#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="$ROOT/uvicorn.pid"
LOG_FILE="$ROOT/uvicorn_fae.log"
VENV_BIN="$ROOT/venv/bin"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8200}"
MYSQL_WAIT_SECONDS="${MYSQL_WAIT_SECONDS:-30}"
MYSQL_WAIT_INTERVAL="${MYSQL_WAIT_INTERVAL:-1}"

# Charger .env si présent pour peupler l'environnement
if [[ -f "$ROOT/.env" ]]; then
    set -a
    # shellcheck disable=SC1090
    . "$ROOT/.env"
    set +a
fi

wait_for_mysql() {
    if [[ "$MYSQL_WAIT_SECONDS" -le 0 ]]; then
        return 0
    fi

    local elapsed=0
    echo "Attente MySQL (max ${MYSQL_WAIT_SECONDS}s)..."
    while (( elapsed < MYSQL_WAIT_SECONDS )); do
        if "$VENV_BIN/python" - <<'PY'
import os
import sys

import pymysql

host = os.getenv("DB_HOST", "127.0.0.1")
port = int(os.getenv("DB_PORT", "3306"))
user = os.getenv("DB_USER", "fae_user")
password = os.getenv("DB_PASS", "change_me")
db = os.getenv("DB_NAME", "fae_afoulki")

try:
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db,
        connect_timeout=2,
    )
    conn.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
        then
            echo "MySQL prêt."
            return 0
        fi
        sleep "$MYSQL_WAIT_INTERVAL"
        elapsed=$((elapsed + MYSQL_WAIT_INTERVAL))
    done

    echo "MySQL indisponible après ${MYSQL_WAIT_SECONDS}s." >&2
    return 1
}

start() {
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "uvicorn déjà démarré (pid $(cat "$PID_FILE"))."
        return 0
    fi
    if [[ -f "$PID_FILE" ]]; then
        rm -f "$PID_FILE"
    fi

    if [[ ! -x "$VENV_BIN/python" ]]; then
        echo "Venv manquante : $VENV_BIN/python introuvable." >&2
        exit 1
    fi

    if ! wait_for_mysql; then
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

find_pids() {
    pgrep -f "uvicorn app.main:app --host $HOST --port $PORT" || true
}

stop() {
    local pid
    local pids=()
    if [[ -f "$PID_FILE" ]]; then
        pid="$(cat "$PID_FILE")"
        if kill -0 "$pid" 2>/dev/null; then
            pids+=("$pid")
        fi
    fi

    local extra_pids
    extra_pids="$(find_pids)"
    if [[ -n "$extra_pids" ]]; then
        while read -r extra_pid; do
            if [[ -n "$extra_pid" ]]; then
                pids+=("$extra_pid")
            fi
        done <<< "$extra_pids"
    fi

    if [[ ${#pids[@]} -eq 0 ]]; then
        echo "Aucun uvicorn trouvé pour $HOST:$PORT."
        rm -f "$PID_FILE"
        return 0
    fi

    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "Arrêt uvicorn (pid $pid)..."
            kill "$pid" || true
        fi
    done
    rm -f "$PID_FILE"
}

status() {
    local pids=()
    local pid
    if [[ -f "$PID_FILE" ]]; then
        pid="$(cat "$PID_FILE")"
        if kill -0 "$pid" 2>/dev/null; then
            pids+=("$pid")
        fi
    fi

    local extra_pids
    extra_pids="$(find_pids)"
    if [[ -n "$extra_pids" ]]; then
        while read -r extra_pid; do
            if [[ -n "$extra_pid" ]]; then
                pids+=("$extra_pid")
            fi
        done <<< "$extra_pids"
    fi

    if [[ ${#pids[@]} -eq 0 ]]; then
        echo "uvicorn arrêté."
        return 0
    fi

    local unique_pids
    unique_pids="$(printf "%s\n" "${pids[@]}" | sort -u | tr '\n' ' ')"
    echo "uvicorn actif (pid(s) $unique_pids) sur $HOST:$PORT. Logs: $LOG_FILE"
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
