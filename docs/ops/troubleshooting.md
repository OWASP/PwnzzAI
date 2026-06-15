# Ollama Connection Troubleshooting (WSL Host + Docker App)

This guide explains how to fix the common error on the Basics page:

`Ollama could not be started. Please check if Ollama is installed or start it manually from https://ollama.ai`

It applies to this setup:
- PwnzzAI app runs in Docker
- Ollama runs on Ubuntu WSL host (not inside the same compose stack)

## Typical Symptoms

In app logs you may see:
- `Ollama is not running or not accessible`
- `Connection refused`
- `External Ollama at http://host.docker.internal:11434 is not reachable`

In browser UI, the Basics page setup button reports Ollama setup failure.

## Root Cause

The app container can resolve `host.docker.internal`, but nothing is accepting connections on port `11434` from the container network. Usually Ollama is only bound to `127.0.0.1` inside WSL.

## Quick Fix

## 1. Start Ollama in WSL on all interfaces

Run in WSL:

```bash
pkill ollama || true
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

Keep this terminal running while testing.

## 2. Start app container with external Ollama host

Run in WSL from repo root:

```bash
sudo PWNZZAI_IMAGE=pwnzzai-local:dev OLLAMA_HOST=http://host.docker.internal:11434 \
  docker compose -f docker-compose.external-ollama.yml up -d --force-recreate
```

If you are not using a local image tag, replace `pwnzzai-local:dev` with your image.

## 3. Verify connectivity from inside app container

The image may not include `curl`; use Python:

```bash
sudo docker exec pwnzzai-shop python -c "import requests; print(requests.get('http://host.docker.internal:11434/api/tags', timeout=5).text)"
```

Expected output: JSON like `{"models":[]}` or a model list.

## 4. Verify the app is reachable

Open:
- `http://localhost:8080`
- Basics page -> click `Setup Ollama`

## Important Compose/Port Notes

- The app listens on container port `8080`.
- Ensure compose publishes `8080:8080`.
- If you changed code, rebuild and run your local image, otherwise compose may still run the registry image.

## Rebuild and run local image (when code changed)

```bash
cd /home/maryam/pwndockerTest/PwnzzAI
sudo docker build --no-cache --pull -t pwnzzai-local:dev .
sudo docker compose -f docker-compose.external-ollama.yml down --remove-orphans
sudo PWNZZAI_IMAGE=pwnzzai-local:dev OLLAMA_HOST=http://host.docker.internal:11434 \
  docker compose -f docker-compose.external-ollama.yml up -d --force-recreate
```

## Confirm running container image/env

```bash
sudo docker inspect pwnzzai-shop --format '{{.Config.Image}} {{.Image}}'
sudo docker inspect pwnzzai-shop --format '{{range .Config.Env}}{{println .}}{{end}}' | grep OLLAMA_HOST
```

## If It Still Fails

Collect and inspect:

```bash
sudo docker compose -f docker-compose.external-ollama.yml logs --tail=120 pwnzzai-app
```

Focus on errors containing:
- `Connection refused` (listener/bind issue)
- `timeout` (routing/firewall issue)
- wrong `OLLAMA_HOST` value (env/config issue)

## Optional: Make Ollama bind persistent in WSL service

If using systemd service for Ollama:

```bash
sudo systemctl edit ollama
```

Add:

```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

Then apply:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
sudo systemctl status ollama
```
