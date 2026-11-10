#!/usr/bin/env bash
# Rebuild and restart only the CTFd container (after changing CTFd-Docker-Challenges/ or compose).
#
# Run from anywhere; uses the PwnzzAI repo this script lives in. Requires Docker.
#
# Usage:
#   ./scripts/ctfd_setup/redeploy-ctfd-workshop.sh
#
# Optional: repo-root .env (same as bootstrap) for CTFD_SECRET_KEY, etc.
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PWNZZAI_ROOT="${PWNZZAI_ROOT:-$ROOT_DIR}"
ENV_FILE="${PWNZZAI_ROOT}/.env"
COMPOSE_FILE="${PWNZZAI_ROOT}/deploy/docker-compose.workshop.yml"

log_info() { printf '[%s] [INFO] %s\n' "$(date -Is)" "$*"; }
log_error() { printf '[%s] [ERROR] %s\n' "$(date -Is)" "$*" >&2; }

if [[ ! -f "$COMPOSE_FILE" ]]; then
  log_error "Cannot find ${COMPOSE_FILE}. Is PWNZZAI_ROOT set correctly?"
  exit 1
fi

if [[ -f "$ENV_FILE" ]]; then
  log_info "Loading ${ENV_FILE}"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi

export COMPOSE_PROFILES="${COMPOSE_PROFILES:-local-ollama}"

# shellcheck source=scripts/ctfd_setup/require-public-host.inc.sh
source "${PWNZZAI_ROOT}/scripts/ctfd_setup/require-public-host.inc.sh"
require_docker_challenges_public_host "${ENV_FILE}"

if ! command -v docker >/dev/null 2>&1; then
  log_error "Docker is not installed or not in your PATH."
  log_error "Install Docker first, or run the full installer: ./scripts/ctfd_setup/bootstrap-ctfd-workshop.sh"
  exit 1
fi

# Prefer docker without sudo; fall back to sudo docker (common when the user is not in the docker group).
if docker info >/dev/null 2>&1; then
  dc() { docker compose "$@"; }
elif command -v sudo >/dev/null 2>&1 && sudo docker info >/dev/null 2>&1; then
  log_info "Using sudo for Docker commands (your account may need to be in the 'docker' group to avoid this)."
  dc() { sudo docker compose "$@"; }
else
  log_error "Cannot talk to Docker. Try one of:"
  log_error "  • Log out and back in after: sudo usermod -aG docker \"\$USER\""
  log_error "  • Or run this script with: sudo $0"
  exit 1
fi

# shellcheck source=scripts/ctfd_setup/workshop-compose-flags.inc.sh
source "${PWNZZAI_ROOT}/scripts/ctfd_setup/workshop-compose-flags.inc.sh"
pwnzzai_set_workshop_compose_flags

log_info "Rebuilding the CTFd image (this can take a minute)..."
cd "${PWNZZAI_ROOT}/deploy"
# Force-refresh plugin clone layers on every redeploy while preserving other Docker cache layers.
DOCKER_CHALLENGES_CACHE_BUSTER="${DOCKER_CHALLENGES_CACHE_BUSTER:-$(date +%s)}"
log_info "Using DOCKER_CHALLENGES_CACHE_BUSTER=${DOCKER_CHALLENGES_CACHE_BUSTER}"
CTFD_SECRET_KEY="${CTFD_SECRET_KEY:-}" DOCKER_CHALLENGES_PUBLIC_HOST="${DOCKER_CHALLENGES_PUBLIC_HOST}" \
  DOCKER_CHALLENGES_CACHE_BUSTER="${DOCKER_CHALLENGES_CACHE_BUSTER}" \
  dc "${PWNZZAI_WORKSHOP_COMPOSE_FLAGS[@]}" build ctfd

log_info "Restarting the CTFd container with the new image..."
# Ensure dependencies are up: redeploy uses --no-deps for ctfd and otherwise can
# leave ctfd running without docker-socket-proxy/ollama after partial restarts.
log_info "Ensuring docker-socket-proxy is running..."
CTFD_SECRET_KEY="${CTFD_SECRET_KEY:-}" DOCKER_CHALLENGES_PUBLIC_HOST="${DOCKER_CHALLENGES_PUBLIC_HOST}" \
  DOCKER_CHALLENGES_CACHE_BUSTER="${DOCKER_CHALLENGES_CACHE_BUSTER}" \
  dc "${PWNZZAI_WORKSHOP_COMPOSE_FLAGS[@]}" up -d docker-socket-proxy
if [[ "${COMPOSE_PROFILES:-local-ollama}" == *local-ollama* ]]; then
  log_info "Ensuring local shared ollama service is running (profile local-ollama)..."
  CTFD_SECRET_KEY="${CTFD_SECRET_KEY:-}" DOCKER_CHALLENGES_PUBLIC_HOST="${DOCKER_CHALLENGES_PUBLIC_HOST}" \
    DOCKER_CHALLENGES_CACHE_BUSTER="${DOCKER_CHALLENGES_CACHE_BUSTER}" \
    dc "${PWNZZAI_WORKSHOP_COMPOSE_FLAGS[@]}" up -d ollama
fi

CTFD_SECRET_KEY="${CTFD_SECRET_KEY:-}" DOCKER_CHALLENGES_PUBLIC_HOST="${DOCKER_CHALLENGES_PUBLIC_HOST}" \
  DOCKER_CHALLENGES_CACHE_BUSTER="${DOCKER_CHALLENGES_CACHE_BUSTER}" \
  dc "${PWNZZAI_WORKSHOP_COMPOSE_FLAGS[@]}" up -d --force-recreate --no-deps ctfd

log_info "Waiting for CTFd to answer on port 8000..."
if command -v curl >/dev/null 2>&1; then
  for _ in $(seq 1 45); do
    if curl -fsS "http://127.0.0.1:8000/" >/dev/null 2>&1; then
      log_info "CTFd is up."
      break
    fi
    sleep 2
  done
else
  log_info "curl not installed; skipped HTTP check. Open http://127.0.0.1:8000 in a browser."
fi

log_info "—"
log_info "Done. CTFd was rebuilt and restarted."
log_info "Open: http://127.0.0.1:8000  (use your server address if this is not this machine.)"
log_info "—"
