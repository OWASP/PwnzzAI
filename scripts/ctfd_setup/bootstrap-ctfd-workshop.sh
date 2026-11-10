#!/usr/bin/env bash
# Bootstrap CTFd + Docker Challenges + shared Ollama + PwnzzAI workshop image on a fresh VM (EC2, etc.).
#
# IMPORTANT (read before use):
# - The CTFd "docker" plugin spawns containers from a pre-built image; it does NOT pass your .env at runtime.
#   This script bakes supported variables from .env into the image at build time (same config for every instance).
# - Per-user unique secrets would require a different plugin or a fork of the Docker Challenges plugin.
#
# Prerequisites: Docker (or permission to install it), Docker Compose plugin, curl for health checks.
# Root/sudo is only used when this script must install system packages or Docker, or when your user cannot
# access the Docker socket (see scripts/ctfd_setup/README.md).
#
# Typical .env keys consumed when building the workshop image (see deploy/Dockerfile.pwnzzai-workshop):
#   SECRET_KEY  GEMINI_API_KEY  GOOGLE_API_KEY  GEMINI_MODEL  LITELLM_MODEL  MODEL_PROVIDER
#   OLLAMA_HOST  OLLAMA_MODEL  OLLAMA_FALLBACK_MODEL  OPENAI_API_KEY  OPENAI_MODEL
#
# Cloud provider selection: the lab route is GEMINI_MODEL (as gemini/...) unless OPENAI_MODEL wins.
# For OpenAI, set OPENAI_API_KEY + OPENAI_MODEL and leave GEMINI_MODEL unset, or set MODEL_PROVIDER=openai
# (or LITELLM_MODEL=openai/<model>) to pin OpenAI explicitly.
#
# Optional:
#   PWNZZAI_ROOT=/path/to/PwnzzAI     (default: repository root — two levels above this script)
#   PWNZZAI_OLLAMA_GPU=0|1            (0=never merge NVIDIA compose; 1=always merge; unset=merge if nvidia-smi works)
#   OLLAMA_HOST                        (default: http://<docker0-gateway>:11434)
#   CTFD_SECRET_KEY                    (recommended for production CTFd)
#   DOCKER_CHALLENGES_PUBLIC_HOST      (public DNS/IP for challenge links — not docker-socket-proxy)
#   DOCKER_CHALLENGES_GIT_URL          (default: northdpole/CTFd-Docker-Challenges.git)
#   DOCKER_CHALLENGES_REF              (default: master)
#
# After this script: open http://<host>:8000, finish the CTFd wizard, configure Docker (see below), then run
#   ./scripts/ctfd_setup/register-pwnzzai-challenge.sh
# with an admin API token to create the PwnzzAI challenge (or create the challenge manually in the UI).
#
# See scripts/ctfd_setup/README.md for full documentation.
#
set -euo pipefail

# Set to 1 after we decide Docker commands need sudo (non-root user without docker group access).
DOCKER_NEEDS_SUDO=0

log_info() { printf '[%s] [INFO] %s\n' "$(date -Is)" "$*"; }
log_warn() { printf '[%s] [WARN] %s\n' "$(date -Is)" "$*" >&2; }
log_error() { printf '[%s] [ERROR] %s\n' "$(date -Is)" "$*" >&2; }

# Kept for backward readability in a few spots.
log() { log_info "$@"; }

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    log_error "Missing required command: $1"
    exit 1
  }
}

detect_docker_bridge_ip() {
  if command -v ip >/dev/null 2>&1; then
    ip -4 addr show docker0 2>/dev/null | awk '/inet / {print $2}' | cut -d/ -f1 | head -1
  fi
}

is_root() { [[ "$(id -u)" -eq 0 ]]; }

explain_sudo_for_system_packages() {
  log_info "—"
  log_info "Administrator privileges are needed next because:"
  log_info "  • Installing OS packages (for example curl) or running the Docker installer writes under system paths"
  log_info "    and configures services; that requires root on this machine."
  log_info "—"
}

explain_sudo_for_docker_install() {
  log_info "—"
  log_info "Administrator privileges are needed next because:"
  log_info "  • Docker Engine is not installed yet. The official installer (get.docker.com) must install"
  log_info "    packages, configure the daemon, and (on systemd) enable the docker service — all root-only steps."
  log_info "—"
}

explain_sudo_for_docker_socket() {
  log_info "—"
  log_info "Administrator privileges are needed for Docker commands because:"
  log_info "  • Your user can run the docker CLI, but cannot talk to the Docker daemon (e.g. not in the"
  log_info "    'docker' group, or the socket permissions exclude this user)."
  log_info "  • This script will use sudo only for docker/docker compose until the end of this run."
  log_info "  • To avoid sudo next time: sudo usermod -aG docker \"\$USER\", then sign out and back in, and re-run."
  log_info "—"
}

ensure_sudo_available() {
  if is_root; then
    return 0
  fi
  if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
    log_info "sudo is available (cached credentials or passwordless)."
    return 0
  fi
  if ! command -v sudo >/dev/null 2>&1; then
    log_error "sudo is not installed and you are not root. Install sudo or re-run as root to install Docker."
    exit 1
  fi
  log_info "You will be prompted for your login password so sudo can perform the steps described above."
  if ! sudo -v; then
    log_error "sudo authentication failed."
    exit 1
  fi
}

install_curl_if_missing() {
  command -v curl >/dev/null 2>&1 && return 0
  log_warn "curl is not installed; it is required for get.docker.com and HTTP checks."
  explain_sudo_for_system_packages
  if is_root; then
    if command -v apt-get >/dev/null 2>&1; then
      apt-get update -y && apt-get install -y curl
    elif command -v dnf >/dev/null 2>&1; then
      dnf install -y curl
    elif command -v yum >/dev/null 2>&1; then
      yum install -y curl
    else
      log_error "Could not install curl automatically. Install curl manually and re-run."
      exit 1
    fi
  else
    ensure_sudo_available
    if command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update -y && sudo apt-get install -y curl
    elif command -v dnf >/dev/null 2>&1; then
      sudo dnf install -y curl
    elif command -v yum >/dev/null 2>&1; then
      sudo yum install -y curl
    else
      log_error "Could not install curl automatically. Install curl manually and re-run."
      exit 1
    fi
  fi
  log_info "curl is now available."
}

install_docker_engine() {
  if command -v docker >/dev/null 2>&1; then
    log_info "Docker CLI already present; skipping get.docker.com."
    return 0
  fi
  explain_sudo_for_docker_install
  install_curl_if_missing
  require_cmd curl
  log_info "Installing Docker Engine via https://get.docker.com ..."
  if is_root; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker 2>/dev/null || true
  else
    ensure_sudo_available
    curl -fsSL https://get.docker.com | sudo sh
    sudo systemctl enable --now docker 2>/dev/null || true
  fi
  log_info "Docker Engine install script finished."
}

docker_info_works() {
  docker info >/dev/null 2>&1
}

sudo_docker_info_works() {
  sudo docker info >/dev/null 2>&1
}

ensure_curl_for_http_checks() {
  command -v curl >/dev/null 2>&1 && return 0
  log_warn "curl is missing; installing it for HTTP checks against CTFd (get.docker.com may have skipped this path)."
  install_curl_if_missing
  require_cmd curl
}

resolve_docker_access() {
  log_info "Checking whether this user can use Docker without sudo..."
  if ! command -v docker >/dev/null 2>&1; then
    log_warn "Docker CLI not found."
    install_docker_engine
  fi
  require_cmd docker

  if is_root; then
    if docker_info_works; then
      log_info "Docker daemon is reachable as root; no sudo wrapper needed for Docker."
      DOCKER_NEEDS_SUDO=0
      return 0
    fi
    log_error "Docker is installed but 'docker info' failed even as root. Is the docker service running?"
    exit 1
  fi

  if docker_info_works; then
    log_info "Docker daemon is reachable without sudo (typical when your user is in the 'docker' group)."
    DOCKER_NEEDS_SUDO=0
    return 0
  fi

  log_warn "'docker info' failed without sudo."
  explain_sudo_for_docker_socket
  if ! command -v sudo >/dev/null 2>&1; then
    log_error "sudo is not available. Add your user to the docker group or run this script as root."
    exit 1
  fi
  log_info "Requesting sudo so we can verify access with: sudo docker info"
  if ! sudo_docker_info_works; then
    log_error "'sudo docker info' also failed. Start the Docker service or fix your installation."
    exit 1
  fi
  DOCKER_NEEDS_SUDO=1
  log_info "Will use sudo for docker and docker compose for the remainder of this script."
}

dock() {
  if [[ "$DOCKER_NEEDS_SUDO" -eq 1 ]]; then
    sudo docker "$@"
  else
    docker "$@"
  fi
}

dcompose() {
  if [[ "$DOCKER_NEEDS_SUDO" -eq 1 ]]; then
    sudo docker compose "$@"
  else
    docker compose "$@"
  fi
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PWNZZAI_ROOT="${PWNZZAI_ROOT:-$ROOT_DIR}"
ENV_FILE="${PWNZZAI_ROOT}/.env"

log_info "Starting CTFd workshop bootstrap (repo: ${PWNZZAI_ROOT})"

if [[ -f "$ENV_FILE" ]]; then
  log_info "Loading environment file: ${ENV_FILE}"
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
else
  log_info "No .env at ${ENV_FILE} yet — you must create one with DOCKER_CHALLENGES_PUBLIC_HOST (see .env.example)."
fi

# Default local shared Ollama container (profile). Empty COMPOSE_PROFILES = no local ollama (remote OLLAMA_HOST only).
export COMPOSE_PROFILES="${COMPOSE_PROFILES:-local-ollama}"

# shellcheck source=scripts/ctfd_setup/require-public-host.inc.sh
source "${PWNZZAI_ROOT}/scripts/ctfd_setup/require-public-host.inc.sh"
require_docker_challenges_public_host "${ENV_FILE}"

BRIDGE_IP="$(detect_docker_bridge_ip || true)"
if [[ -z "${OLLAMA_HOST:-}" ]]; then
  if [[ -n "$BRIDGE_IP" ]]; then
    OLLAMA_HOST="http://${BRIDGE_IP}:11434"
  else
    OLLAMA_HOST="http://172.17.0.1:11434"
  fi
  log_info "OLLAMA_HOST not set; default for spawned challenge containers: ${OLLAMA_HOST}"
fi

resolve_docker_access

log_info "Docker is ready; verifying with a quick docker info (quiet)."
dock info >/dev/null
log_info "Docker check OK."

ensure_curl_for_http_checks

WORKSHOP_TAG="${PWNZZAI_WORKSHOP_IMAGE:-pwnzzai-workshop:latest}"

log_info "Building PwnzzAI workshop image tag: ${WORKSHOP_TAG}"
log_info "OLLAMA_HOST baked into image: ${OLLAMA_HOST}"

dock build \
  -f "${PWNZZAI_ROOT}/deploy/Dockerfile.pwnzzai-workshop" \
  --build-arg "SECRET_KEY=${SECRET_KEY:-}" \
  --build-arg "GEMINI_API_KEY=${GEMINI_API_KEY:-}" \
  --build-arg "GOOGLE_API_KEY=${GOOGLE_API_KEY:-}" \
  --build-arg "GEMINI_MODEL=${GEMINI_MODEL:-}" \
  --build-arg "LITELLM_MODEL=${LITELLM_MODEL:-}" \
  --build-arg "MODEL_PROVIDER=${MODEL_PROVIDER:-auto}" \
  --build-arg "OLLAMA_HOST=${OLLAMA_HOST}" \
  --build-arg "OLLAMA_MODEL=${OLLAMA_MODEL:-mistral:7b}" \
  --build-arg "OLLAMA_FALLBACK_MODEL=${OLLAMA_FALLBACK_MODEL:-llama3.2:1b}" \
  --build-arg "OPENAI_API_KEY=${OPENAI_API_KEY:-}" \
  --build-arg "OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o-mini}" \
  --build-arg "ALLOW_PRECONFIGURED_OPENAI_KEY=${ALLOW_PRECONFIGURED_OPENAI_KEY:-true}" \
  --build-arg "PREFER_SESSION_OPENAI_KEY=${PREFER_SESSION_OPENAI_KEY:-true}" \
  --build-arg "MODEL_TIMEOUT_SECONDS=${MODEL_TIMEOUT_SECONDS:-60}" \
  --build-arg "ENABLE_PROVIDER_FALLBACK=${ENABLE_PROVIDER_FALLBACK:-true}" \
  -t "$WORKSHOP_TAG" \
  "$PWNZZAI_ROOT"

log_info "Starting CTFd stack (docker compose in ${PWNZZAI_ROOT}/deploy)"
cd "${PWNZZAI_ROOT}/deploy"
# shellcheck source=scripts/ctfd_setup/workshop-compose-flags.inc.sh
source "${PWNZZAI_ROOT}/scripts/ctfd_setup/workshop-compose-flags.inc.sh"
pwnzzai_set_workshop_compose_flags
if [[ "${#PWNZZAI_WORKSHOP_COMPOSE_FLAGS[@]}" -gt 2 ]]; then
  log_info "Compose includes docker-compose.workshop.nvidia.yml (Ollama GPU request)."
else
  log_info "Compose is CPU-only for Ollama (no nvidia merge). Set PWNZZAI_OLLAMA_GPU=0 to force, or =1 if you use NVIDIA."
fi
CTFD_SECRET_KEY="${CTFD_SECRET_KEY:-}" DOCKER_CHALLENGES_PUBLIC_HOST="${DOCKER_CHALLENGES_PUBLIC_HOST}" \
  dcompose "${PWNZZAI_WORKSHOP_COMPOSE_FLAGS[@]}" up -d --build

log_info "Waiting for CTFd HTTP on http://127.0.0.1:8000 ..."
for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:8000/setup" >/dev/null 2>&1 || curl -fsS "http://127.0.0.1:8000/" >/dev/null 2>&1; then
    log_info "CTFd responded over HTTP."
    break
  fi
  sleep 2
done

log_info "Bootstrap finished successfully."
log_info "—"
log_info "NEXT STEPS (challenge is NOT registered yet):"
log_info "  1) Open http://<this-host>:8000 and complete the CTFd setup wizard if prompted."
log_info "  2) Admin → Settings → API Tokens → create a token (copy it somewhere safe)."
log_info "  3) Run the second script to apply Docker API settings (docker-socket-proxy:2375) and register the challenge:"
log_info "       export CTFD_API_TOKEN='your-token-here'"
log_info "       ${PWNZZAI_ROOT}/scripts/ctfd_setup/register-pwnzzai-challenge.sh"
log_info "     (Optional: put CTFD_API_TOKEN in ${ENV_FILE} and run the script without export.)"
log_info "     Registration uses docker compose exec to set Docker Config in the ctfd DB; use CTFD_SKIP_DOCKER_CONFIG=1 for remote CTFd."
log_info "  Alternatively: Admin → Challenges → New → type \"docker\" → image ${WORKSHOP_TAG}"
log_info "—"
log_info "Workshop image tag (use in step 4 or manual challenge): ${WORKSHOP_TAG}"
