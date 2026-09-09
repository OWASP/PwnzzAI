#!/usr/bin/env python3
"""
Create (or update) a **standard** CTFd challenge that links participants to ONE shared
PwnzzAI instance.

Use this instead of ``register_pwnzzai_challenge.py`` when CTFd runs somewhere without a
Docker daemon — for example the two-pod deployment in ``deploy/deploy-pod-*.sh``, where
provider pods are containers themselves. The docker_challenges plugin cannot spawn
per-participant containers there, so a single shared instance is linked from a standard
challenge (the "Shared lab URL" option in ``scripts/ctfd_setup/README.md``).

Unlike the docker variant, this script is idempotent: re-running it updates the existing
challenge with the same name instead of creating duplicates.

Environment:
  CTFD_URL          CTFd base URL (default http://127.0.0.1:8000)
  CTFD_API_TOKEN    Admin API token (alias: CTFD_API_KEY) — required
  PWNZZAI_URL       URL participants open for the shared app — required
                    (or set PWNZZAI_PUBLIC_HOST [+ PWNZZAI_PUBLIC_PORT, default 8080])
  CHALLENGE_NAME    Challenge name (default "PwnzzAI Workshop")
  CHALLENGE_CATEGORY  (default "Workshop")
  CHALLENGE_VALUE   Points (default 1)
  CHALLENGE_FLAG    Optional static flag to attach (skipped if the challenge already has flags)

Usage:
  CTFD_URL=http://127.0.0.1:8000 CTFD_API_TOKEN=xxx \
  PWNZZAI_URL=http://app-pod-host:8080 \
    python3 deploy/register_pwnzzai_standard_challenge.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_NAME = "PwnzzAI Workshop"


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _merge_repo_dotenv() -> None:
    """Fill missing os.environ keys from repo-root .env (same behaviour as the docker variant)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.is_file():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def _request(url: str, token: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=_headers(token), method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = resp.read().decode()
    return json.loads(body) if body else {}


def resolve_app_url() -> str:
    url = (os.environ.get("PWNZZAI_URL") or "").strip().rstrip("/")
    if url:
        return url
    host = (
        os.environ.get("PWNZZAI_PUBLIC_HOST")
        or os.environ.get("DOCKER_CHALLENGES_PUBLIC_HOST")
        or ""
    ).strip()
    if not host:
        return ""
    port = (os.environ.get("PWNZZAI_PUBLIC_PORT") or "8080").strip()
    return f"http://{host}:{port}"


def find_challenge_id(base: str, token: str, name: str) -> int | None:
    """Return the id of the challenge with this exact name, or None."""
    body: dict | None = None
    for query in ("?view=admin", ""):
        try:
            body = _request(f"{base}/api/v1/challenges{query}", token)
            break
        except urllib.error.HTTPError as e:
            if e.code not in (400, 404):
                print(f"HTTP {e.code} listing challenges: {e.read().decode(errors='replace')}",
                      file=sys.stderr)
                raise
    if not body or not body.get("success"):
        return None
    for row in body.get("data") or []:
        if row.get("name") == name:
            return int(row["id"])
    return None


def challenge_has_flags(base: str, token: str, challenge_id: int) -> bool:
    try:
        body = _request(f"{base}/api/v1/challenges/{challenge_id}/flags", token)
    except urllib.error.HTTPError:
        return False
    return bool(body.get("data"))


def main() -> int:
    _merge_repo_dotenv()

    base = (os.environ.get("CTFD_URL") or "http://127.0.0.1:8000").rstrip("/")
    token = (os.environ.get("CTFD_API_TOKEN") or os.environ.get("CTFD_API_KEY") or "").strip()
    name = (os.environ.get("CHALLENGE_NAME") or DEFAULT_NAME).strip()
    category = (os.environ.get("CHALLENGE_CATEGORY") or "Workshop").strip()
    flag = (os.environ.get("CHALLENGE_FLAG") or "").strip()
    try:
        value = int(os.environ.get("CHALLENGE_VALUE") or "1")
    except ValueError:
        print("CHALLENGE_VALUE must be an integer.", file=sys.stderr)
        return 1

    if not token:
        print("CTFD_API_TOKEN is required (Admin -> Settings -> API Tokens).", file=sys.stderr)
        return 1

    app_url = resolve_app_url()
    if not app_url:
        print(
            "PWNZZAI_URL is required — the URL participants open for the shared PwnzzAI app "
            "(e.g. http://app-pod-host:8080). Alternatively set PWNZZAI_PUBLIC_HOST "
            "(+ PWNZZAI_PUBLIC_PORT).",
            file=sys.stderr,
        )
        return 1

    description = (
        f"Open the shared PwnzzAI lab: {app_url}\n\n"
        "This is **one shared instance** for the whole workshop — there is no per-user "
        "container to start, so application state and flags are visible to everyone. "
        "Work through the labs in the app and submit the flag you find here."
    )
    payload = {
        "name": name,
        "category": category,
        "description": description,
        "value": value,
        "type": "standard",
        "state": "visible",
        "max_attempts": 0,
        "connection_info": app_url,
    }

    try:
        existing = find_challenge_id(base, token, name)
    except Exception:
        return 1

    try:
        if existing is not None:
            body = _request(f"{base}/api/v1/challenges/{existing}", token, "PATCH", payload)
            if not body.get("success"):
                print(json.dumps(body, indent=2), file=sys.stderr)
                return 1
            chal_id = existing
            print(f"Updated challenge id={chal_id} ({name}) -> {app_url}")
        else:
            body = _request(f"{base}/api/v1/challenges", token, "POST", payload)
            if not body.get("success"):
                print(json.dumps(body, indent=2), file=sys.stderr)
                return 1
            chal_id = int(body["data"]["id"])
            print(f"Created challenge id={chal_id} ({name}) -> {app_url}")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code} writing challenge: {e.read().decode(errors='replace')}",
              file=sys.stderr)
        return 1
    except urllib.error.URLError as e:
        print(f"Cannot reach CTFd at {base}: {e.reason}", file=sys.stderr)
        print("Has the CTFd setup wizard been completed? Is CTFD_URL correct?", file=sys.stderr)
        return 1

    if flag:
        if challenge_has_flags(base, token, chal_id):
            print("Challenge already has a flag; leaving it unchanged.")
            return 0
        try:
            body = _request(
                f"{base}/api/v1/flags",
                token,
                "POST",
                {"challenge_id": chal_id, "content": flag, "type": "static", "data": ""},
            )
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code} creating flag: {e.read().decode(errors='replace')}",
                  file=sys.stderr)
            return 1
        if not body.get("success"):
            print(json.dumps(body, indent=2), file=sys.stderr)
            return 1
        print("Flag created.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
