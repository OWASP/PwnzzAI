#!/usr/bin/env bash
# Pod 1 of 2 — GPU pod: install and run Ollama natively inside this container.
#
# Run this INSIDE the GPU pod (provider web terminal or `ssh` into the pod). It uses no
# Docker and no systemd: the Ollama binary is installed to a prefix on this filesystem and
# `ollama serve` is supervised with nohup + a PID file.
#
# Usage (inside the GPU pod, from the repo root):
#   ./deploy/pod-deployment/deploy-pod-ollama.sh            # same as `up`
#   ./deploy/pod-deployment/deploy-pod-ollama.sh up         # install + serve + pull models + verify
#   ./deploy/pod-deployment/deploy-pod-ollama.sh pull       # pull/refresh models only
#   ./deploy/pod-deployment/deploy-pod-ollama.sh status     # is it running?
#   ./deploy/pod-deployment/deploy-pod-ollama.sh verify     # probe the API and loaded models
#   ./deploy/pod-deployment/deploy-pod-ollama.sh logs       # follow the serve log
#   ./deploy/pod-deployment/deploy-pod-ollama.sh stop | restart
#
# Environment:
#   OLLAMA_BIND                 Bind address for `ollama serve` (default 0.0.0.0:11434).
#                               Must be 0.0.0.0 so the app pod can reach it.
#   OLLAMA_MODEL                Primary model (default mistral:7b)
#   OLLAMA_FALLBACK_MODEL       Secondary model (default llama3.2:1b)
#   PWNZZAI_EXTRA_MODELS        Space-separated extra tags to pull (optional)
#   OLLAMA_MODELS               Model storage dir (default <state>/ollama-models)
#   PWNZZAI_POD_STATE_DIR       State dir (default /workspace/.pwnzzai, else ~/.pwnzzai)
#   PWNZZAI_OLLAMA_PREFIX       Install prefix (default /usr/local, else <state>/ollama)
#   PWNZZAI_SKIP_MODEL_SMOKE=1  Skip the "generate one token" check after pulling
#
# IMPORTANT (provider port exposure): the pod must expose TCP 11434 for the app pod to
# reach it. On RunPod that means adding 11434 to the pod's exposed TCP ports when you
# create the pod; the provider then gives you a public host:port to use as OLLAMA_HOST on
# the app pod. Exposing an unauthenticated Ollama endpoint publicly means anyone who finds
# it can use your GPU — restrict it to the app pod's address if your provider allows it.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# shellcheck source=deploy/pod-common.inc.sh
source "${SCRIPT_DIR}/pod-common.inc.sh"

# Repo .env may define OLLAMA_HOST as a *client* URL for the app pod. That value must not
# reach `ollama serve`, which reads OLLAMA_HOST as its *bind* address, so it is overridden
# from OLLAMA_BIND below.
pod_load_dotenv "${ROOT_DIR}/.env"

STATE_DIR="$(pod_default_state_dir)"
RUN_DIR="${STATE_DIR}/run"
LOG_DIR="${STATE_DIR}/logs"
PIDFILE="${RUN_DIR}/ollama.pid"
LOGFILE="${LOG_DIR}/ollama.log"

OLLAMA_BIND="${OLLAMA_BIND:-0.0.0.0:11434}"
OLLAMA_PORT="${OLLAMA_BIND##*:}"
LOCAL_API="http://127.0.0.1:${OLLAMA_PORT}"

PRIMARY_MODEL="${OLLAMA_MODEL:-mistral:7b}"
FALLBACK_MODEL="${OLLAMA_FALLBACK_MODEL:-llama3.2:1b}"
EXTRA_MODELS="${PWNZZAI_EXTRA_MODELS:-}"

export OLLAMA_MODELS="${OLLAMA_MODELS:-${STATE_DIR}/ollama-models}"
# Keep the model resident so the first participant request is not a cold load.
export OLLAMA_KEEP_ALIVE="${OLLAMA_KEEP_ALIVE:--1}"

OLLAMA_BIN=""

# --------------------------------------------------------------------------------------

resolve_ollama_bin() {
  local prefix_bin
  if [[ -n "${PWNZZAI_OLLAMA_PREFIX:-}" && -x "${PWNZZAI_OLLAMA_PREFIX}/bin/ollama" ]]; then
    OLLAMA_BIN="${PWNZZAI_OLLAMA_PREFIX}/bin/ollama"
    return 0
  fi
  prefix_bin="${STATE_DIR}/ollama/bin/ollama"
  if [[ -x "$prefix_bin" ]]; then
    OLLAMA_BIN="$prefix_bin"
    return 0
  fi
  if command -v ollama >/dev/null 2>&1; then
    OLLAMA_BIN="$(command -v ollama)"
    return 0
  fi
  return 1
}

report_gpu() {
  if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then
    pod_log_info "GPU(s) visible to this pod:"
    nvidia-smi -L || true
  else
    pod_log_warn "No GPU detected (nvidia-smi missing or lists nothing). Ollama will run on CPU:"
    pod_log_warn "  mistral:7b on CPU answers in tens of seconds — consider OLLAMA_MODEL=llama3.2:1b."
  fi
}

# Unpack the Ollama release tarball into <prefix>, using sudo/root only for the extract
# step when <prefix> is not writable by the current user.
install_ollama_tarball() {
  local prefix="$1" arch url tmp rc=0
  case "$(uname -m)" in
    x86_64 | amd64) arch="amd64" ;;
    aarch64 | arm64) arch="arm64" ;;
    *)
      pod_log_error "Unsupported architecture for the Ollama tarball: $(uname -m)"
      return 1
      ;;
  esac
  url="https://ollama.com/download/ollama-linux-${arch}.tgz"

  pod_log_info "Downloading ${url}"
  tmp="$(mktemp -d)"
  # shellcheck disable=SC2064
  trap "rm -rf '${tmp}'" RETURN
  if ! curl -fsSL --retry 3 -o "${tmp}/ollama.tgz" "$url"; then
    pod_log_error "Download failed: ${url}"
    return 1
  fi

  pod_log_info "Extracting Ollama into ${prefix}"
  if [[ -w "$prefix" ]] || mkdir -p "$prefix" 2>/dev/null; then
    tar -xzf "${tmp}/ollama.tgz" -C "$prefix" || rc=$?
  else
    pod_sudo mkdir -p "$prefix" && pod_sudo tar -xzf "${tmp}/ollama.tgz" -C "$prefix" || rc=$?
  fi
  if ((rc != 0)) || [[ ! -x "${prefix}/bin/ollama" ]]; then
    pod_log_warn "Could not install Ollama into ${prefix}"
    return 1
  fi
  return 0
}

ensure_ollama_installed() {
  if resolve_ollama_bin; then
    pod_log_info "Ollama already installed: ${OLLAMA_BIN} ($("${OLLAMA_BIN}" --version 2>/dev/null | head -n1 || echo 'version unknown'))"
    return 0
  fi

  command -v curl >/dev/null 2>&1 || pod_apt_install curl ca-certificates || true
  command -v curl >/dev/null 2>&1 || {
    pod_log_error "curl is required to install Ollama."
    return 1
  }
  command -v tar >/dev/null 2>&1 || pod_apt_install tar || true

  # Unpack the release tarball ourselves. The official install.sh installs a systemd unit;
  # in a container that step fails and the script can exit non-zero even when the binary
  # landed, so we do not depend on it.
  local prefix="${PWNZZAI_OLLAMA_PREFIX:-/usr/local}"
  if ! install_ollama_tarball "$prefix"; then
    if [[ "$prefix" == "${STATE_DIR}/ollama" ]]; then
      pod_log_error "Ollama install failed."
      return 1
    fi
    prefix="${STATE_DIR}/ollama"
    pod_log_warn "Falling back to a user-writable prefix: ${prefix}"
    install_ollama_tarball "$prefix" || {
      pod_log_error "Ollama install failed."
      return 1
    }
  fi

  export PWNZZAI_OLLAMA_PREFIX="$prefix"
  resolve_ollama_bin || {
    pod_log_error "Ollama binary still not found after install."
    return 1
  }
  pod_log_info "Installed Ollama: ${OLLAMA_BIN}"
  return 0
}

start_serve() {
  mkdir -p "$OLLAMA_MODELS" "$RUN_DIR" "$LOG_DIR"

  if pod_service_running "$PIDFILE"; then
    pod_log_info "ollama serve already running (pid $(cat "$PIDFILE"))"
    return 0
  fi

  if pod_port_in_use "$OLLAMA_PORT"; then
    pod_log_warn "Port ${OLLAMA_PORT} is already bound by another process (not started by this script)."
    if pod_wait_http "${LOCAL_API}/api/tags" 1 1; then
      pod_log_info "An Ollama API is already answering on ${LOCAL_API}; reusing it."
      return 0
    fi
    pod_log_error "Port ${OLLAMA_PORT} is busy but does not serve the Ollama API. Free it or set OLLAMA_BIND."
    return 1
  fi

  # `ollama serve` reads OLLAMA_HOST as its listen address (not as a client URL).
  OLLAMA_HOST="$OLLAMA_BIND" \
  pod_service_start "ollama" "$PIDFILE" "$LOGFILE" "$STATE_DIR" "$OLLAMA_BIN" serve

  pod_log_info "Waiting for the Ollama API on ${LOCAL_API}"
  if ! pod_wait_http "${LOCAL_API}/api/tags" 60 2; then
    pod_log_error "Ollama did not answer on ${LOCAL_API}. Last 40 log lines:"
    tail -n 40 "$LOGFILE" >&2 2>/dev/null || true
    return 1
  fi
  pod_log_info "Ollama API is up on ${LOCAL_API} (bind ${OLLAMA_BIND}, models in ${OLLAMA_MODELS})"
  return 0
}

model_list() {
  local models=("$PRIMARY_MODEL")
  if [[ -n "$FALLBACK_MODEL" && "$FALLBACK_MODEL" != "$PRIMARY_MODEL" ]]; then
    models+=("$FALLBACK_MODEL")
  fi
  local extra
  for extra in $EXTRA_MODELS; do
    models+=("$extra")
  done
  printf '%s\n' "${models[@]}"
}

pull_models() {
  local model
  while IFS= read -r model; do
    [[ -n "$model" ]] || continue
    pod_log_info "Pulling model: ${model} (this can take several minutes)"
    # Client mode: point the CLI at the local API, never at the bind wildcard.
    if ! OLLAMA_HOST="127.0.0.1:${OLLAMA_PORT}" "$OLLAMA_BIN" pull "$model"; then
      pod_log_error "Failed to pull ${model}"
      return 1
    fi
  done < <(model_list)

  pod_log_info "Models available on this pod:"
  OLLAMA_HOST="127.0.0.1:${OLLAMA_PORT}" "$OLLAMA_BIN" list || true
  return 0
}

smoke_model() {
  if [[ "${PWNZZAI_SKIP_MODEL_SMOKE:-0}" == "1" ]]; then
    pod_log_info "Skipping model smoke test (PWNZZAI_SKIP_MODEL_SMOKE=1)"
    return 0
  fi
  pod_log_info "Smoke-testing generation with ${PRIMARY_MODEL} (one token)"
  local payload
  payload="$(printf '{"model":"%s","prompt":"ping","stream":false,"options":{"num_predict":1}}' "$PRIMARY_MODEL")"
  if curl -fsS --max-time 300 -H 'Content-Type: application/json' \
      -d "$payload" "${LOCAL_API}/api/generate" >/dev/null 2>&1; then
    pod_log_info "Generation OK — the model loads and responds."
  else
    # Not fatal: a cold CPU load of a 7B model can exceed the timeout while still being fine.
    pod_log_warn "Generation probe did not finish in time. Check '${0##*/} logs' before the workshop."
  fi
  return 0
}

print_next_steps() {
  local ip
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  cat <<EOF

================================================================================
GPU pod ready — Ollama is serving on ${OLLAMA_BIND}
================================================================================
  Models     : $(model_list | tr '\n' ' ')
  Model dir  : ${OLLAMA_MODELS}
  Log        : ${LOGFILE}
  Pod-local  : ${LOCAL_API}${ip:+  (pod IP: http://${ip}:${OLLAMA_PORT})}

Next: on the APP pod, run the app deployment with this pod's *externally reachable*
Ollama URL. Take the public host:port your provider maps to TCP ${OLLAMA_PORT} for this
pod (RunPod: "Connect" -> TCP port mappings) and run, from the repo root:

  OLLAMA_HOST=http://<gpu-pod-public-host>:<mapped-port> \\
  OLLAMA_MODEL=${PRIMARY_MODEL} \\
  PWNZZAI_PUBLIC_HOST=<app-pod-public-host> \\
    ./deploy/pod-deployment/deploy-pod-app.sh

Verify from the app pod first:
  curl -fsS http://<gpu-pod-public-host>:<mapped-port>/api/tags
================================================================================
EOF
}

cmd_up() {
  report_gpu
  ensure_ollama_installed
  start_serve
  pull_models
  smoke_model
  print_next_steps
}

cmd_verify() {
  resolve_ollama_bin || {
    pod_log_error "Ollama is not installed on this pod. Run: ${0##*/} up"
    return 1
  }
  pod_service_status "ollama" "$PIDFILE"
  if ! curl -fsS --max-time 10 "${LOCAL_API}/api/tags"; then
    pod_log_error "Ollama API is not answering on ${LOCAL_API}"
    return 1
  fi
  printf '\n'
  smoke_model
}

main() {
  local cmd="${1:-up}"
  mkdir -p "$RUN_DIR" "$LOG_DIR"
  case "$cmd" in
    up) cmd_up ;;
    pull)
      resolve_ollama_bin || { pod_log_error "Ollama not installed; run: ${0##*/} up"; exit 1; }
      start_serve
      pull_models
      ;;
    status) pod_service_status "ollama" "$PIDFILE" ;;
    verify) cmd_verify ;;
    logs) pod_service_logs "$LOGFILE" "${2:-80}" ;;
    stop) pod_service_stop "ollama" "$PIDFILE" ;;
    restart)
      pod_service_stop "ollama" "$PIDFILE"
      resolve_ollama_bin || { pod_log_error "Ollama not installed; run: ${0##*/} up"; exit 1; }
      start_serve
      ;;
    -h | --help | help)
      sed -n '2,40p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      ;;
    *)
      pod_log_error "Unknown command: ${cmd}"
      pod_log_error "Usage: ${0##*/} [up|pull|status|verify|logs|stop|restart]"
      exit 2
      ;;
  esac
}

main "$@"
