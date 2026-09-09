# shellcheck shell=bash
# Shared helpers for the two-pod (no-Docker) deployment scripts:
#   deploy/deploy-pod-ollama.sh   — GPU pod: Ollama
#   deploy/deploy-pod-app.sh      — app pod: PwnzzAI Flask
#   deploy/deploy-pod-ctfd.sh     — app pod: CTFd (shared-instance challenge)
#
# These scripts run *inside* an already-running container ("pod") on providers like
# RunPod / Vast.ai. There is no dockerd and no systemd, so services are started with
# nohup + PID files instead of `docker compose` or `systemctl`.
#
# Source from a script:
#   source "$(dirname "${BASH_SOURCE[0]}")/pod-common.inc.sh"

pod_log_info()  { printf '[%s] [INFO] %s\n'  "$(date -Is)" "$*"; }
pod_log_warn()  { printf '[%s] [WARN] %s\n'  "$(date -Is)" "$*" >&2; }
pod_log_error() { printf '[%s] [ERROR] %s\n' "$(date -Is)" "$*" >&2; }

# --------------------------------------------------------------------------------------
# Environment / paths
# --------------------------------------------------------------------------------------

# Run a command as root when possible. Returns 127 when neither root nor sudo is available
# (common in provider pods, where callers should degrade to a warning instead of failing).
pod_sudo() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    return 127
  fi
}

# Persistent state (venvs, model blobs, PID files, logs). Provider pods usually mount a
# persistent volume at /workspace; everything else on the pod is lost when it restarts.
pod_default_state_dir() {
  if [[ -n "${PWNZZAI_POD_STATE_DIR:-}" ]]; then
    printf '%s\n' "${PWNZZAI_POD_STATE_DIR}"
  elif [[ -d /workspace && -w /workspace ]]; then
    printf '%s\n' /workspace/.pwnzzai
  else
    printf '%s\n' "${HOME:-/root}/.pwnzzai"
  fi
}

# Load KEY=VALUE lines from a .env file without overriding what is already exported,
# so `OLLAMA_HOST=... ./deploy-pod-app.sh` always wins over the file.
pod_load_dotenv() {
  local env_file="$1"
  [[ -f "$env_file" ]] || return 0

  local raw line key val
  while IFS= read -r raw || [[ -n "$raw" ]]; do
    line="${raw#"${raw%%[![:space:]]*}"}"
    [[ -z "$line" || "$line" == \#* ]] && continue
    [[ "$line" == export\ * ]] && line="${line#export }"
    [[ "$line" == *=* ]] || continue
    key="${line%%=*}"
    val="${line#*=}"
    key="${key%"${key##*[![:space:]]}"}"
    val="${val#"${val%%[![:space:]]*}"}"
    val="${val%"${val##*[![:space:]]}"}"
    # Strip one layer of matching quotes.
    if [[ "$val" == \"*\" || "$val" == \'*\' ]]; then
      val="${val:1:${#val}-2}"
    fi
    [[ -n "$key" ]] || continue
    [[ -n "${!key+x}" ]] && continue
    export "${key}=${val}"
  done <"$env_file"
}

pod_gen_secret() {
  if command -v openssl >/dev/null 2>&1; then
    openssl rand -hex 32
  elif command -v python3 >/dev/null 2>&1; then
    python3 -c 'import secrets; print(secrets.token_hex(32))'
  else
    # Last resort; adequate for a workshop, not for production secrets.
    date +%s%N | sha256sum | cut -d' ' -f1
  fi
}

# Install Debian/Ubuntu packages if apt-get is usable. Never fatal: a pod without apt
# still runs the app, it just loses the optional pieces (e.g. QR decoding).
pod_apt_install() {
  local pkgs=("$@")
  ((${#pkgs[@]})) || return 0

  if ! command -v apt-get >/dev/null 2>&1; then
    pod_log_warn "apt-get not available; install manually if needed: ${pkgs[*]}"
    return 1
  fi

  pod_log_info "Installing system packages: ${pkgs[*]}"
  if ! DEBIAN_FRONTEND=noninteractive pod_sudo apt-get update -qq; then
    pod_log_warn "apt-get update failed (no root/sudo or no network); skipping: ${pkgs[*]}"
    return 1
  fi
  if ! DEBIAN_FRONTEND=noninteractive pod_sudo apt-get install -y --no-install-recommends "${pkgs[@]}"; then
    pod_log_warn "apt-get install failed; continuing without: ${pkgs[*]}"
    return 1
  fi
  return 0
}

# --------------------------------------------------------------------------------------
# Health checks
# --------------------------------------------------------------------------------------

pod_wait_http() {
  local url="$1" retries="${2:-60}" sleep_seconds="${3:-2}" i
  for ((i = 1; i <= retries; i++)); do
    if curl -fsS --max-time 10 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$sleep_seconds"
  done
  return 1
}

pod_port_in_use() {
  local port="$1"
  if command -v ss >/dev/null 2>&1; then
    ss -ltn 2>/dev/null | grep -qE "[:.]${port}[[:space:]]"
  elif command -v netstat >/dev/null 2>&1; then
    netstat -ltn 2>/dev/null | grep -qE "[:.]${port}[[:space:]]"
  else
    return 1
  fi
}

# --------------------------------------------------------------------------------------
# Process supervision (no systemd in a container)
# --------------------------------------------------------------------------------------

pod_service_running() {
  local pidfile="$1" pid
  [[ -f "$pidfile" ]] || return 1
  pid="$(cat "$pidfile" 2>/dev/null || true)"
  [[ -n "$pid" ]] || return 1
  kill -0 "$pid" 2>/dev/null
}

# pod_service_start <name> <pidfile> <logfile> <workdir> <cmd> [args...]
# The child inherits the caller's exported environment, so export config before calling.
pod_service_start() {
  local name="$1" pidfile="$2" logfile="$3" workdir="$4"
  shift 4

  if pod_service_running "$pidfile"; then
    pod_log_info "${name} already running (pid $(cat "$pidfile"))"
    return 0
  fi

  mkdir -p "$(dirname "$pidfile")" "$(dirname "$logfile")"
  pod_log_info "Starting ${name} (log: ${logfile})"
  # nohup so the service survives the SSH / web-terminal session that launched it.
  ( cd "$workdir" && nohup "$@" >>"$logfile" 2>&1 & echo $! >"$pidfile" )
  sleep 2

  if ! pod_service_running "$pidfile"; then
    pod_log_error "${name} exited immediately. Last 40 lines of ${logfile}:"
    tail -n 40 "$logfile" >&2 2>/dev/null || true
    return 1
  fi
  pod_log_info "${name} running (pid $(cat "$pidfile"))"
  return 0
}

pod_service_stop() {
  local name="$1" pidfile="$2" pid i
  if ! pod_service_running "$pidfile"; then
    pod_log_info "${name} is not running"
    rm -f "$pidfile"
    return 0
  fi
  pid="$(cat "$pidfile")"
  pod_log_info "Stopping ${name} (pid ${pid})"
  kill "$pid" 2>/dev/null || true
  for ((i = 0; i < 15; i++)); do
    kill -0 "$pid" 2>/dev/null || break
    sleep 1
  done
  if kill -0 "$pid" 2>/dev/null; then
    pod_log_warn "${name} did not exit on SIGTERM; sending SIGKILL"
    kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$pidfile"
  return 0
}

pod_service_status() {
  local name="$1" pidfile="$2"
  if pod_service_running "$pidfile"; then
    printf '%-12s running   pid=%s\n' "$name" "$(cat "$pidfile")"
  else
    printf '%-12s stopped\n' "$name"
  fi
}

pod_service_logs() {
  local logfile="$1" lines="${2:-80}"
  if [[ -f "$logfile" ]]; then
    tail -n "$lines" -f "$logfile"
  else
    pod_log_error "No log file at ${logfile}"
    return 1
  fi
}
