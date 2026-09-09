#!/usr/bin/env bash
# App pod — CTFd scoreboard, installed from source and run natively (no Docker, no systemd).
#
# WHY THIS IS NOT THE WORKSHOP CTFd: deploy/docker-compose.workshop.yml runs CTFd with the
# docker_challenges plugin, which spawns one container per participant through the Docker
# API. That needs a Docker daemon, which a provider pod does not have. This script therefore
# installs plain CTFd and registers ONE standard challenge that links to the single shared
# PwnzzAI instance on this pod — the "Shared lab URL" option in scripts/ctfd_setup/README.md.
# Trade-off: participants share one app instance, so app state and flags are shared too.
#
# Normally invoked by deploy/deploy-pod-app.sh; can be run on its own.
#
# Usage (inside the app pod, from the repo root):
#   ./deploy/deploy-pod-ctfd.sh up          # clone + venv + start + wait
#   ./deploy/deploy-pod-ctfd.sh register    # create/update the shared-instance challenge
#   ./deploy/deploy-pod-ctfd.sh status | verify | logs | stop | restart
#
# Environment:
#   PWNZZAI_URL             URL participants open for the shared app
#                           (default http://${PWNZZAI_PUBLIC_HOST}:${PWNZZAI_PUBLIC_PORT:-8080})
#   PWNZZAI_PUBLIC_HOST     Public host/IP of this pod (no http://)
#   CTFD_PORT               CTFd port (default 8000)
#   CTFD_PUBLIC_PORT        Provider-mapped public port for CTFD_PORT (default same)
#   CTFD_VERSION            CTFd git tag to install (default 3.7.7 — matches the workshop image)
#   CTFD_SECRET_KEY         CTFd secret (generated once into the state dir if unset)
#   CTFD_WORKERS            gunicorn workers (default 2)
#   CTFD_API_TOKEN          Admin API token; required only for `register`
#   CHALLENGE_NAME          Challenge name (default "PwnzzAI Workshop")
#   CHALLENGE_FLAG          Optional static flag to attach
#   PWNZZAI_POD_STATE_DIR   State dir (default /workspace/.pwnzzai, else ~/.pwnzzai)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# shellcheck source=deploy/pod-common.inc.sh
source "${SCRIPT_DIR}/pod-common.inc.sh"

pod_load_dotenv "${ROOT_DIR}/.env"

STATE_DIR="$(pod_default_state_dir)"
RUN_DIR="${STATE_DIR}/run"
LOG_DIR="${STATE_DIR}/logs"
PIDFILE="${RUN_DIR}/ctfd.pid"
LOGFILE="${LOG_DIR}/ctfd.log"

CTFD_VERSION="${CTFD_VERSION:-3.7.7}"
CTFD_PORT="${CTFD_PORT:-8000}"
CTFD_PUBLIC_PORT="${CTFD_PUBLIC_PORT:-$CTFD_PORT}"
CTFD_SRC="${CTFD_SRC:-${STATE_DIR}/CTFd-${CTFD_VERSION}}"
CTFD_VENV="${CTFD_VENV:-${STATE_DIR}/ctfd-venv}"
CTFD_DATA="${CTFD_DATA:-${STATE_DIR}/ctfd-data}"
CTFD_SECRET_FILE="${STATE_DIR}/ctfd-secret-key"
CTFD_WORKERS="${CTFD_WORKERS:-2}"
LOCAL_CTFD="http://127.0.0.1:${CTFD_PORT}"

PWNZZAI_PUBLIC_HOST="${PWNZZAI_PUBLIC_HOST:-${DOCKER_CHALLENGES_PUBLIC_HOST:-127.0.0.1}}"
PWNZZAI_URL="${PWNZZAI_URL:-http://${PWNZZAI_PUBLIC_HOST}:${PWNZZAI_PUBLIC_PORT:-8080}}"
CTFD_URL_LOCAL="$LOCAL_CTFD"
CTFD_URL_PUBLIC="http://${PWNZZAI_PUBLIC_HOST}:${CTFD_PUBLIC_PORT}"

# --------------------------------------------------------------------------------------

resolve_ctfd_secret() {
  if [[ -z "${CTFD_SECRET_KEY:-}" ]]; then
    if [[ -f "$CTFD_SECRET_FILE" ]]; then
      CTFD_SECRET_KEY="$(cat "$CTFD_SECRET_FILE")"
    else
      CTFD_SECRET_KEY="$(pod_gen_secret)"
      mkdir -p "$STATE_DIR"
      umask 077
      printf '%s\n' "$CTFD_SECRET_KEY" >"$CTFD_SECRET_FILE"
      pod_log_info "Generated a CTFd secret key into ${CTFD_SECRET_FILE}"
    fi
  fi
  export CTFD_SECRET_KEY
}

fetch_ctfd() {
  command -v git >/dev/null 2>&1 || pod_apt_install git ca-certificates || true
  command -v git >/dev/null 2>&1 || {
    pod_log_error "git is required to install CTFd from source."
    exit 1
  }

  if [[ -d "${CTFD_SRC}/CTFd" ]]; then
    pod_log_info "Reusing CTFd source at ${CTFD_SRC}"
    return 0
  fi
  pod_log_info "Cloning CTFd ${CTFD_VERSION} into ${CTFD_SRC}"
  rm -rf "$CTFD_SRC"
  mkdir -p "$(dirname "$CTFD_SRC")"
  git clone --depth 1 --branch "$CTFD_VERSION" https://github.com/CTFd/CTFd.git "$CTFD_SRC" || {
    pod_log_error "Clone of CTFd ${CTFD_VERSION} failed. Check the tag exists and the pod has network access."
    exit 1
  }
}

build_ctfd_venv() {
  # A separate venv on purpose: CTFd 3.7.x pins Flask 2.x while the app needs Flask 3.1.0,
  # so the two cannot share one environment.
  if [[ ! -x "${CTFD_VENV}/bin/python" ]]; then
    pod_log_info "Creating CTFd virtualenv at ${CTFD_VENV}"
    python3 -m venv "$CTFD_VENV" || {
      pod_log_error "venv creation failed. On Debian/Ubuntu: apt-get install -y python3-venv"
      exit 1
    }
  else
    pod_log_info "Reusing CTFd virtualenv at ${CTFD_VENV}"
  fi

  if [[ -f "${CTFD_VENV}/.requirements-installed" ]]; then
    pod_log_info "CTFd requirements already installed (remove ${CTFD_VENV}/.requirements-installed to redo)"
    return 0
  fi

  "${CTFD_VENV}/bin/python" -m pip install --upgrade --no-cache-dir pip setuptools wheel
  pod_log_info "Installing CTFd requirements (a few minutes on a cold pod)"
  "${CTFD_VENV}/bin/pip" install --no-cache-dir --retries 10 --timeout 600 \
    -r "${CTFD_SRC}/requirements.txt" || {
    pod_log_error "CTFd dependency install failed."
    pod_log_error "Most common cause: the pod's Python is newer than CTFd ${CTFD_VERSION} supports."
    pod_log_error "CTFd 3.7.x targets Python 3.11. Options:"
    pod_log_error "  - use a pod image with Python 3.11, or"
    pod_log_error "  - skip CTFd (PWNZZAI_WITH_CTFD=0) and hand out the app URL directly."
    exit 1
  }
  # CTFd ships gunicorn in requirements, but do not assume it across tags.
  if [[ ! -x "${CTFD_VENV}/bin/gunicorn" ]]; then
    "${CTFD_VENV}/bin/pip" install --no-cache-dir gunicorn || true
  fi
  touch "${CTFD_VENV}/.requirements-installed"
}

export_ctfd_env() {
  resolve_ctfd_secret
  mkdir -p "${CTFD_DATA}/uploads"
  export DATABASE_URL="${CTFD_DATABASE_URL:-sqlite:///${CTFD_DATA}/ctfd.db}"
  export UPLOAD_FOLDER="${CTFD_DATA}/uploads"
  export SECRET_KEY="$CTFD_SECRET_KEY"
  # No Redis on this pod: keep CTFd on its filesystem/simple cache and turn off SSE, which
  # would otherwise pin a sync gunicorn worker per connected browser.
  export SERVER_SENT_EVENTS="${SERVER_SENT_EVENTS:-false}"
  export REVERSE_PROXY="${REVERSE_PROXY:-false}"
}

start_ctfd() {
  if pod_service_running "$PIDFILE"; then
    pod_log_info "CTFd already running (pid $(cat "$PIDFILE"))"
    return 0
  fi
  if pod_port_in_use "$CTFD_PORT"; then
    pod_log_error "Port ${CTFD_PORT} is already bound. Free it or set CTFD_PORT."
    exit 1
  fi

  export_ctfd_env

  if [[ -x "${CTFD_VENV}/bin/gunicorn" ]]; then
    pod_service_start "ctfd" "$PIDFILE" "$LOGFILE" "$CTFD_SRC" \
      "${CTFD_VENV}/bin/gunicorn" "CTFd:create_app()" \
      --bind "0.0.0.0:${CTFD_PORT}" --workers "$CTFD_WORKERS" --timeout 120
  else
    pod_log_warn "gunicorn unavailable; falling back to CTFd's serve.py (development server)"
    pod_service_start "ctfd" "$PIDFILE" "$LOGFILE" "$CTFD_SRC" \
      "${CTFD_VENV}/bin/python" serve.py --host 0.0.0.0 --port "$CTFD_PORT"
  fi

  pod_log_info "Waiting for CTFd on ${LOCAL_CTFD}"
  # A fresh install answers on /setup; an initialised one answers on /.
  if ! pod_wait_http "${LOCAL_CTFD}/setup" 90 2 && ! pod_wait_http "${LOCAL_CTFD}/" 5 2; then
    pod_log_error "CTFd did not become reachable. Last 60 lines of ${LOGFILE}:"
    tail -n 60 "$LOGFILE" >&2 2>/dev/null || true
    exit 1
  fi
  pod_log_info "CTFd is serving on ${LOCAL_CTFD}"
}

cmd_register() {
  local token="${CTFD_API_TOKEN:-${CTFD_API_KEY:-}}"
  if [[ -z "$token" ]]; then
    pod_log_error "CTFD_API_TOKEN is required to register the challenge."
    pod_log_error "Finish the CTFd setup wizard at ${CTFD_URL_PUBLIC}, then"
    pod_log_error "Admin -> Settings -> API Tokens, and re-run:"
    pod_log_error "  CTFD_API_TOKEN=xxx ./deploy/deploy-pod-ctfd.sh register"
    exit 1
  fi
  pod_log_info "Registering the shared-instance challenge pointing at ${PWNZZAI_URL}"
  CTFD_URL="${CTFD_URL:-$CTFD_URL_LOCAL}" \
  CTFD_API_TOKEN="$token" \
  PWNZZAI_URL="$PWNZZAI_URL" \
    python3 "${SCRIPT_DIR}/register_pwnzzai_standard_challenge.py"
}

print_next_steps() {
  cat <<EOF

================================================================================
CTFd ready on port ${CTFD_PORT} (shared-instance mode — no per-user containers)
================================================================================
  Scoreboard   : ${CTFD_URL_PUBLIC}
  Shared app   : ${PWNZZAI_URL}
  CTFd source  : ${CTFD_SRC} (tag ${CTFD_VERSION})
  CTFd data    : ${CTFD_DATA} (SQLite DB + uploads)
  Log          : ${LOGFILE}

Remaining manual steps (CTFd requires its wizard to run once):
  1. Open ${CTFD_URL_PUBLIC} and complete the setup wizard (admin account, event name).
  2. Admin -> Settings -> API Tokens -> generate a token.
  3. Register the challenge that links participants to the shared app:
       CTFD_API_TOKEN=<token> ./deploy/deploy-pod-ctfd.sh register

  Do NOT create a "docker" type challenge — that plugin is absent here by design,
  because this pod has no Docker daemon.
================================================================================
EOF
}

cmd_up() {
  fetch_ctfd
  build_ctfd_venv
  start_ctfd
  print_next_steps
}

main() {
  local cmd="${1:-up}"
  mkdir -p "$RUN_DIR" "$LOG_DIR"
  case "$cmd" in
    up) cmd_up ;;
    register) cmd_register ;;
    status) pod_service_status "ctfd" "$PIDFILE" ;;
    verify)
      pod_service_status "ctfd" "$PIDFILE"
      curl -fsS --max-time 15 "${LOCAL_CTFD}/" >/dev/null 2>&1 \
        || curl -fsS --max-time 15 "${LOCAL_CTFD}/setup" >/dev/null 2>&1 \
        || { pod_log_error "CTFd is not answering on ${LOCAL_CTFD}"; exit 1; }
      pod_log_info "[OK] CTFd responds on ${LOCAL_CTFD}"
      ;;
    logs) pod_service_logs "$LOGFILE" "${2:-80}" ;;
    stop) pod_service_stop "ctfd" "$PIDFILE" ;;
    restart)
      pod_service_stop "ctfd" "$PIDFILE"
      start_ctfd
      ;;
    -h | --help | help)
      sed -n '2,35p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      ;;
    *)
      pod_log_error "Unknown command: ${cmd}"
      pod_log_error "Usage: ${0##*/} [up|register|status|verify|logs|stop|restart]"
      exit 2
      ;;
  esac
}

main "$@"
