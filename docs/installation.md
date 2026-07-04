# Installation Guide

Choose one of these 3 ways to run PwnzzAI:

1. Docker with both images (PwnzzAI + Ollama)
2. Docker with your own local/remote Ollama and only the PwnzzAI image
3. Run the source code yourself

## Before You Start (All Options)

1. Install Docker Desktop from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop).
2. Open Docker Desktop and wait until it says Docker is running.
3. Install Git if you do not already have it.
4. Clone this repository and enter it:

```bash
git clone https://github.com/OWASP/PwnzzAI.git
cd PwnzzAI
```

## Option 1: Docker (PwnzzAI + Ollama)

Use this option if you want Docker to run both the PwnzzAI app and Ollama for you.

1. Start both containers:

```bash
docker compose up -d
```

2. Verify both services are running:

```bash
docker compose ps
```

3. Open the app in your browser:

```
http://localhost:8080
```

4. In the app, go to the Basics page and run Ollama setup to pull models.

5. Follow logs if needed:

```bash
# App logs
docker compose logs -f pwnzzai-app

# Ollama logs (optional)
docker compose logs -f ollama
```

6. Stop everything when done:

```bash
docker compose down
```

7. Optional full reset (removes saved Ollama models too):

```bash
docker compose down -v
```

## Option 2: Docker (Your Own Ollama + PwnzzAI Image)

Use this option if Ollama is already running somewhere else and you only want to run PwnzzAI in Docker.

1. Keep your Ollama service running.

2. If Ollama is on a **remote** machine, set `OLLAMA_HOST` before starting:

=== "Linux/macOS"

    ```bash
    export OLLAMA_HOST=http://your-ollama-server:11434
    ```

=== "Windows PowerShell"

    ```powershell
    $env:OLLAMA_HOST="http://your-ollama-server:11434"
    ```

3. Start PwnzzAI with the external-Ollama compose file:

```bash
docker compose -f docker-compose.external-ollama.yml up -d
```

4. Visit `http://localhost:8080` in your browser to see the application.

5. Follow app logs if needed:

```bash
docker compose -f docker-compose.external-ollama.yml logs -f pwnzzai-app
```

6. Stop it when done:

```bash
docker compose -f docker-compose.external-ollama.yml down
```

## Option 3: Run Source Code Yourself

Use this option if you want to run Python directly (without Docker for the app).

1. Install Python 3.11.

2. Create and activate a virtual environment:

=== "Linux/macOS"

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

=== "Windows PowerShell"

    ```powershell
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    ```

3. Install dependencies:

```bash
./install.sh
```

4. Make sure Ollama is available at `http://localhost:11434` or another endpoint via `OLLAMA_HOST`.

5. Run the app:

```bash
flask run --host=0.0.0.0 --port=8080
```

6. Open:

```
http://localhost:8080
```

## Optional: Configure a Cloud Model

The labs run on a free local model out of the box. To also use the **cloud model** tabs (OpenAI / Gemini / Claude), you need **two** things — an API key **and** a model name:

- **API key** — can be entered at runtime via the in-app *Lab Setup* page, **or** set in `.env` (`OPENAI_API_KEY=...`). The key from Lab Setup takes precedence.
- **Model name** — has **no UI**; it must come from `.env`. There is no default in code, so calls fail with `LLM Provider NOT provided` if it is unset.

Create `.env` from the template and uncomment the model line:

```bash
cp .env.example .env
# then edit .env and set, for example:
#   OPENAI_MODEL=gpt-4o-mini
#   (or LITELLM_MODEL=gemini/gemini-2.5-flash, etc.)
```

Restart the app after editing `.env`.

## Troubleshooting

If you run Ollama on WSL and PwnzzAI in Docker, see the [OLLAMA_CONNECTION_TROUBLESHOOTING.md](https://github.com/OWASP/PwnzzAI/blob/main/OLLAMA_CONNECTION_TROUBLESHOOTING.md) for connectivity fixes.

## Cloud LLM Setup

For detailed instructions on configuring cloud AI providers (OpenAI, Claude, Gemini), see the [Workshop Cloud LLM Setup Guide](https://github.com/OWASP/PwnzzAI/blob/main/docs/workshop-cloud-llm-setup.md).
