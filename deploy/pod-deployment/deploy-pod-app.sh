#!/usr/bin/env bash
# Pod 2 of 2 — app pod: install and run the PwnzzAI Flask app natively inside this container.
#
# Run this INSIDE the app pod, from the repository root. It uses no Docker and no systemd:
# dependencies go into a venv on this filesystem and `flask run` is supervised with
# nohup + a PID file. Inference is delegated to the GPU pod over OLLAMA_HOST.
#
# Usage (inside the app pod, from the repo root):
#   OLLAMA_HOST=http://<gpu-pod-host>:<port> PWNZZAI_PUBLIC_HOST=<app-pod-host> \
#     ./deploy/deploy-pod-app.sh              # same as `up`
#
#   ./deploy/deploy-pod-app.sh up             # deps + venv + start + verify (+ CTFd)
#   ./deploy/deploy-pod-app.sh status         # is it running?
#   ./deploy/deploy-pod-app.sh verify         # probe the app and its Ollama link
#   ./deploy/deploy-pod-app.sh logs           # follow the app log
#   ./deploy/deploy-pod-app.sh stop | restart
#
# Environment:
#   OLLAMA_HOST                 REQUIRED — URL of the GPU pod's Ollama, e.g.
#                               http://gpu-pod-host:11434 (must not be localhost)
#   OLLAMA_MODEL                Primary model, must exist on the GPU pod (default mistral:7b)
#   OLLAMA_FALLBACK_MODEL       Secondary model (default llama3.2:1b)
#   PWNZZAI_PUBLIC_HOST         Public host/IP participants type in a browser (no http://).
#                               Used for printed links and the CTFd challenge link.
#   PWNZZAI_PORT                App port (default 8080)
#   PWNZZAI_PUBLIC_PORT         Provider-mapped public port for PWNZZAI_PORT (default same)
#   SECRET_KEY                  Flask secret (generated once into the state dir if unset)
#   MODEL_PROVIDER              auto | ollama | openai (default ollama for this deployment)
#   PWNZZAI_WITH_CTFD           1 (default) also deploy CTFd via deploy-pod-ctfd.sh, 0 to skip
#   PWNZZAI_POD_STATE_DIR       State dir (default /workspace/.pwnzzai, else ~/.pwnzzai)
#   PWNZZAI_VENV                Virtualenv path (default <state>/venv)
#   PWNZZAI_SKIP_TORCH=1        Do not preinstall CPU torch (only if torch is already present)
#   PWNZZAI_SKIP_INSTALL=1      Skip apt/pip entirely (fast restart of an already-built pod)
#   PWNZZAI_REQUIRE_MODEL=0     Do not fail when OLLAMA_MODEL is missing on the GPU pod
#
# IMPORTANT (provider port exposure): the pod must expose TCP ${PWNZZAI_PORT:-8080}
# (and 8000 when CTFd is enabled) for participants to reach it. On RunPod, add those ports
# to the pod's exposed HTTP/TCP ports at creation time.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# shellcheck source=deploy/pod-common.inc.sh
source "${SCRIPT_DIR}/pod-common.inc.sh"

pod_load_dotenv "${ROOT_DIR}/.env"

STATE_DIR="$(pod_default_state_dir)"
RUN_DIR="${STATE_DIR}/run"
LOG_DIR="${STATE_DIR}/logs"
PIDFILE="${RUN_DIR}/pwnzzai-app.pid"
LOGFILE="${LOG_DIR}/pwnzzai-app.log"
SECRET_FILE="${STATE_DIR}/app-secret-key"
POD_ENV_FILE="${STATE_DIR}/pwnzzai-pod.env"

VENV="${PWNZZAI_VENV:-${STATE_DIR}/venv}"
APP_PORT="${PWNZZAI_PORT:-8080}"
PUBLIC_PORT="${PWNZZAI_PUBLIC_PORT:-$APP_PORT}"
LOCAL_APP="http://127.0.0.1:${APP_PORT}"
TORCH_INDEX_URL="${PWNZZAI_TORCH_INDEX_URL:-https://download.pytorch.org/whl/cpu}"

# --------------------------------------------------------------------------------------
# Configuration checks
# --------------------------------------------------------------------------------------

require_ollama_host() {
  local host="${OLLAMA_HOST:-}" hostname_only
  host="${host%/}"

  if [[ -z "$host" ]]; then
    pod_log_error "OLLAMA_HOST is not set."
    pod_log_error "This pod runs the Flask app only; inference lives on the GPU pod."
    pod_log_error "Set it to the GPU pod's externally reachable Ollama URL, e.g.:"
    pod_log_error "  OLLAMA_HOST=http://gpu-pod-host:11434 ./deploy/deploy-pod-app.sh"
    exit 1
  fi
  if [[ "$host" != http://* && "$host" != https://* ]]; then
    pod_log_error "OLLAMA_HOST must include a scheme, e.g. http://gpu-pod-host:11434 (got: ${host})"
    exit 1
  fi

  hostname_only="${host#*://}"
  hostname_only="${hostname_only%%[:/]*}"
  if [[ "${PWNZZAI_ALLOW_LOCAL_OLLAMA:-0}" != "1" ]]; then
    case "$hostname_only" in
      localhost | 127.0.0.1 | ::1 | 0.0.0.0)
        pod_log_error "OLLAMA_HOST points at this pod (${host}), but Ollama runs on the OTHER pod."
        pod_log_error "Use the GPU pod's public host:port. Override with PWNZZAI_ALLOW_LOCAL_OLLAMA=1"
        pod_log_error "only if you really are running Ollama inside this same pod."
        exit 1
        ;;
    esac
  fi

  export OLLAMA_HOST="$host"
}

check_ollama_link() {
  pod_log_info "Checking the GPU pod's Ollama at ${OLLAMA_HOST}"
  local tags
  if ! tags="$(curl -fsS --max-time 15 "${OLLAMA_HOST}/api/tags" 2>/dev/null)"; then
    pod_log_error "Cannot reach ${OLLAMA_HOST}/api/tags from this pod."
    pod_log_error "Checklist:"
    pod_log_error "  1. On the GPU pod: ./deploy/deploy-pod-ollama.sh status"
    pod_log_error "  2. Ollama must bind 0.0.0.0 (OLLAMA_BIND=0.0.0.0:11434), not 127.0.0.1"
    pod_log_error "  3. The GPU pod must EXPOSE TCP 11434 and you must use the provider-mapped"
    pod_log_error "     public host:port here (pod-to-pod private networking is usually off)"
    pod_log_error "  4. See OLLAMA_CONNECTION_TROUBLESHOOTING.md"
    exit 1
  fi
  pod_log_info "Ollama reachable. Models reported by the GPU pod:"
  printf '%s\n' "$tags" | grep -o '"name":"[^"]*"' | sed 's/"name":"/  - /; s/"$//' || printf '%s\n' "$tags"

  if [[ "${PWNZZAI_REQUIRE_MODEL:-1}" == "1" ]] \
      && ! printf '%s' "$tags" | grep -q "\"${OLLAMA_MODEL}\""; then
    pod_log_error "Model '${OLLAMA_MODEL}' is not present on the GPU pod."
    pod_log_error "On the GPU pod run: OLLAMA_MODEL=${OLLAMA_MODEL} ./deploy/deploy-pod-ollama.sh pull"
    pod_log_error "Or set PWNZZAI_REQUIRE_MODEL=0 to deploy anyway (labs will fail until it exists)."
    exit 1
  fi
}

resolve_config() {
  export OLLAMA_MODEL="${OLLAMA_MODEL:-mistral:7b}"
  export OLLAMA_FALLBACK_MODEL="${OLLAMA_FALLBACK_MODEL:-llama3.2:1b}"
  # This deployment has a dedicated Ollama pod; default to it rather than `auto`, which
  # would prefer OpenAI whenever a key happens to be present in the environment.
  export MODEL_PROVIDER="${MODEL_PROVIDER:-ollama}"
  export MODEL_TIMEOUT_SECONDS="${MODEL_TIMEOUT_SECONDS:-120}"
  export ENABLE_PROVIDER_FALLBACK="${ENABLE_PROVIDER_FALLBACK:-true}"
  export FLASK_APP="${FLASK_APP:-main.py}"
  export PYTHONUNBUFFERED=1
  # Ask the GPU pod to keep the model resident between requests.
  export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:--1}"

  if [[ -z "${SECRET_KEY:-}" ]]; then
    if [[ -f "$SECRET_FILE" ]]; then
      SECRET_KEY="$(cat "$SECRET_FILE")"
    else
      SECRET_KEY="$(pod_gen_secret)"
      mkdir -p "$STATE_DIR"
      umask 077
      printf '%s\n' "$SECRET_KEY" >"$SECRET_FILE"
      pod_log_info "Generated a Flask SECRET_KEY into ${SECRET_FILE}"
    fi
  fi
  export SECRET_KEY

  if [[ -z "${PWNZZAI_PUBLIC_HOST:-}" ]]; then
    PWNZZAI_PUBLIC_HOST="${DOCKER_CHALLENGES_PUBLIC_HOST:-}"
  fi
  if [[ -z "${PWNZZAI_PUBLIC_HOST:-}" ]]; then
    pod_log_warn "PWNZZAI_PUBLIC_HOST is not set; printed links and the CTFd challenge link"
    pod_log_warn "will use 127.0.0.1, which participants cannot open. Set it to this pod's public host."
    PWNZZAI_PUBLIC_HOST="127.0.0.1"
  fi
  export PWNZZAI_PUBLIC_HOST
  export PWNZZAI_URL="${PWNZZAI_URL:-http://${PWNZZAI_PUBLIC_HOST}:${PUBLIC_PORT}}"
}

# Persist the resolved config so `restart` (or a pod reboot) reuses the same values.
write_pod_env_file() {
  mkdir -p "$STATE_DIR"
  umask 077
  {
    printf '# Written by deploy/deploy-pod-app.sh — resolved config for the PwnzzAI app pod.\n'
    printf '# Sourced on restart. Edit here and run: ./deploy/deploy-pod-app.sh restart\n'
    local key
    for key in OLLAMA_HOST OLLAMA_MODEL OLLAMA_FALLBACK_MODEL OLLAMA_KEEP_ALIVE \
               MODEL_PROVIDER MODEL_TIMEOUT_SECONDS ENABLE_PROVIDER_FALLBACK \
               SECRET_KEY FLASK_APP PWNZZAI_PUBLIC_HOST PWNZZAI_URL \
               PWNZZAI_PORT PWNZZAI_PUBLIC_PORT \
               OPENAI_API_KEY OPENAI_MODEL GEMINI_API_KEY GEMINI_MODEL LITELLM_MODEL; do
      [[ -n "${!key:-}" ]] && printf '%s=%s\n' "$key" "${!key}"
    done
    printf 'PWNZZAI_PORT=%s\n' "$APP_PORT"
    printf 'PWNZZAI_PUBLIC_PORT=%s\n' "$PUBLIC_PORT"
  } >"$POD_ENV_FILE"
  pod_log_info "Resolved config written to ${POD_ENV_FILE}"
}

# --------------------------------------------------------------------------------------
# Install
# --------------------------------------------------------------------------------------

install_system_deps() {
  # libzbar0 is the runtime for pyzbar (QR-code labs). Everything else in
  # requirements.txt ships manylinux wheels, so no compiler is needed.
  if ! pod_apt_install libzbar0; then
    pod_log_warn "libzbar0 not installed — the QR-code labs will fail on import of pyzbar."
  fi
  command -v curl >/dev/null 2>&1 || pod_apt_install curl ca-certificates || true
  command -v git >/dev/null 2>&1 || pod_apt_install git || true
}

check_python() {
  command -v python3 >/dev/null 2>&1 || {
    pod_log_error "python3 not found in this pod. Install Python 3.11 first."
    exit 1
  }
  local ver
  ver="$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
  pod_log_info "Using python3 ${ver} ($(command -v python3))"
  case "$ver" in
    3.10 | 3.11 | 3.12) ;;
    *)
      pod_log_warn "requirements.txt is pinned for Python 3.11 (the app image uses python:3.11-slim)."
      pod_log_warn "Python ${ver} may fail to resolve numpy==1.26.4 / sentence-transformers==5.0.0."
      ;;
  esac
}

build_venv() {
  if [[ "${PWNZZAI_SKIP_INSTALL:-0}" == "1" ]]; then
    pod_log_info "PWNZZAI_SKIP_INSTALL=1 — skipping apt/pip"
    [[ -x "${VENV}/bin/python" ]] || {
      pod_log_error "No venv at ${VENV}; cannot skip install on a fresh pod."
      exit 1
    }
    return 0
  fi

  if [[ ! -x "${VENV}/bin/python" ]]; then
    pod_log_info "Creating virtualenv at ${VENV}"
    python3 -m venv "$VENV" || {
      pod_log_error "venv creation failed. On Debian/Ubuntu: apt-get install -y python3-venv"
      exit 1
    }
  else
    pod_log_info "Reusing virtualenv at ${VENV}"
  fi

  "${VENV}/bin/python" -m pip install --upgrade --no-cache-dir pip

  if [[ "${PWNZZAI_SKIP_TORCH:-0}" != "1" ]]; then
    # CPU torch first, exactly as the Dockerfile does, so sentence-transformers does not
    # pull the CUDA wheel (~GB of nvidia-* packages) onto a pod that never runs inference.
    pod_log_info "Installing CPU-only torch from ${TORCH_INDEX_URL}"
    "${VENV}/bin/pip" install --no-cache-dir --retries 10 --timeout 600 \
      torch --index-url "$TORCH_INDEX_URL"
  fi

  pod_log_info "Installing requirements.txt (a few minutes on a cold pod)"
  "${VENV}/bin/pip" install --no-cache-dir --retries 10 --timeout 600 \
    -r "${ROOT_DIR}/requirements.txt"
}

prepare_app_dirs() {
  # instance/pizza_shop.db is opened via a RELATIVE path by several labs, so the app must
  # always run with CWD=repo root (see start_app).
  mkdir -p "${ROOT_DIR}/uploads" "${ROOT_DIR}/downloads" "${ROOT_DIR}/instance"
}

# --------------------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------------------

start_app() {
  if pod_service_running "$PIDFILE"; then
    pod_log_info "PwnzzAI app already running (pid $(cat "$PIDFILE")); restarting to apply config"
    pod_service_stop "pwnzzai-app" "$PIDFILE"
  fi

  if pod_port_in_use "$APP_PORT"; then
    pod_log_error "Port ${APP_PORT} is already bound by another process. Free it or set PWNZZAI_PORT."
    exit 1
  fi

  pod_service_start "pwnzzai-app" "$PIDFILE" "$LOGFILE" "$ROOT_DIR" \
    "${VENV}/bin/python" -m flask run --host=0.0.0.0 --port="$APP_PORT" --no-reload

  pod_log_info "Waiting for the app on ${LOCAL_APP}"
  if ! pod_wait_http "${LOCAL_APP}/" 60 2; then
    pod_log_error "App did not become reachable. Last 60 lines of ${LOGFILE}:"
    tail -n 60 "$LOGFILE" >&2 2>/dev/null || true
    exit 1
  fi
  pod_log_info "App is serving on ${LOCAL_APP}"
}

verify_app() {
  local ok=0
  pod_service_status "pwnzzai-app" "$PIDFILE"

  if curl -fsS --max-time 15 "${LOCAL_APP}/" >/dev/null 2>&1; then
    pod_log_info "[OK] App root responds on ${LOCAL_APP}/"
  else
    pod_log_error "[FAIL] App root does not respond on ${LOCAL_APP}/"
    ok=1
  fi

  # The app's own view of the model backend — this is the check that catches a broken
  # OLLAMA_HOST baked into a running process.
  if curl -fsS --max-time 60 "${LOCAL_APP}/check-ollama-status" >/dev/null 2>&1; then
    pod_log_info "[OK] /check-ollama-status responds (app can talk to ${OLLAMA_HOST})"
  else
    pod_log_warn "[WARN] /check-ollama-status did not respond cleanly; check ${LOGFILE}"
    ok=1
  fi
  return "$ok"
}

maybe_deploy_ctfd() {
  if [[ "${PWNZZAI_WITH_CTFD:-1}" != "1" ]]; then
    pod_log_info "PWNZZAI_WITH_CTFD=0 — skipping CTFd. The app is usable directly at ${PWNZZAI_URL}"
    return 0
  fi
  pod_log_info "Deploying CTFd on this pod (shared-instance challenge pointing at ${PWNZZAI_URL})"
  PWNZZAI_URL="$PWNZZAI_URL" PWNZZAI_PUBLIC_HOST="$PWNZZAI_PUBLIC_HOST" \
    "${SCRIPT_DIR}/deploy-pod-ctfd.sh" up
}

print_next_steps() {
  cat <<EOF

================================================================================
App pod ready — PwnzzAI is serving on port ${APP_PORT}
================================================================================
  Participants open : ${PWNZZAI_URL}
  Model backend     : ${OLLAMA_HOST} (model ${OLLAMA_MODEL}, fallback ${OLLAMA_FALLBACK_MODEL})
  Provider          : ${MODEL_PROVIDER}
  Virtualenv        : ${VENV}
  Resolved config   : ${POD_ENV_FILE}
  Log               : ${LOGFILE}

Management:
  ./deploy/deploy-pod-app.sh status | verify | logs | restart | stop

If ${PWNZZAI_URL} does not open from outside the pod, the port is not exposed by the
provider — add TCP/HTTP ${APP_PORT} to this pod's exposed ports and use the mapped
public port as PWNZZAI_PUBLIC_PORT.
================================================================================
EOF
}

cmd_up() {
  require_ollama_host
  resolve_config
  check_ollama_link
  install_system_deps
  check_python
  build_venv
  prepare_app_dirs
  write_pod_env_file
  start_app
  verify_app || pod_log_warn "Verification reported problems; see above."
  print_next_steps
  maybe_deploy_ctfd
}

# For status/verify/restart/logs: reuse the config persisted by the last `up`.
load_persisted_config() {
  pod_load_dotenv "$POD_ENV_FILE"
  APP_PORT="${PWNZZAI_PORT:-$APP_PORT}"
  PUBLIC_PORT="${PWNZZAI_PUBLIC_PORT:-$APP_PORT}"
  LOCAL_APP="http://127.0.0.1:${APP_PORT}"
  export OLLAMA_HOST="${OLLAMA_HOST:-unset}"
}

main() {
  local cmd="${1:-up}"
  mkdir -p "$RUN_DIR" "$LOG_DIR"
  case "$cmd" in
    up) cmd_up ;;
    status)
      load_persisted_config
      pod_service_status "pwnzzai-app" "$PIDFILE"
      ;;
    verify)
      load_persisted_config
      verify_app
      ;;
    logs) pod_service_logs "$LOGFILE" "${2:-80}" ;;
    stop) pod_service_stop "pwnzzai-app" "$PIDFILE" ;;
    restart)
      [[ -f "$POD_ENV_FILE" ]] || {
        pod_log_error "No saved config at ${POD_ENV_FILE}. Run a full deploy first:"
        pod_log_error "  OLLAMA_HOST=http://<gpu-pod-host>:<port> ./deploy/deploy-pod-app.sh up"
        exit 1
      }
      load_persisted_config
      require_ollama_host
      resolve_config
      start_app
      verify_app || true
      ;;
    -h | --help | help)
      sed -n '2,45p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      ;;
    *)
      pod_log_error "Unknown command: ${cmd}"
      pod_log_error "Usage: ${0##*/} [up|status|verify|logs|stop|restart]"
      exit 2
      ;;
  esac
}

main "$@"
