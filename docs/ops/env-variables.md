# Environment Variables Reference

Full reference for all environment variables used by PwnzzAI. The canonical
source of truth is `.env.example` at the repo root — this doc adds precedence
rules and interaction notes that don't fit in inline comments.

## Usage

Copy `.env.example` to `.env` in the repo root and edit:

```bash
cp .env.example .env
```

The app reads from `os.environ` on startup. For Docker, set them as
environment variables in the compose file or pass them at runtime.

## LLM Provider Model Resolution

This is the most complex part of the config. There are **three resolution chains**
depending on what you're configuring, and they interact in subtle ways.

### Chain 1: Global Default (`resolved_litellm_model()`)

Used for: Lab Setup UI, fallback when lab-specific vars are unset.

```
LITELLM_MODEL (full route, e.g. "gemini/gemini-3.1-flash-lite")
    ↓ if unset
GEMINI_MODEL (bare id → "gemini/<id>", or full route if contains "/")
    ↓ if unset
OPENAI_MODEL (bare id → "openai/<id>")
    ↓ if unset
"" (empty — cloud calls fail with "LLM Provider NOT provided")
```

### Chain 2: Most Cloud Labs (`lab_cloud_llm_model_default()`)

Used for: prompt injection, insecure plugin, RAG, DoS, order access, etc.

```
LAB_CLOUD_LLM_MODEL
    ↓ if unset
GEMINI_MODEL (→ "gemini/<id>" or full route)
    ↓ if unset
OPENAI_MODEL (bare id)
    ↓ if unset
"" (empty — cloud calls fail)
```

### Chain 3: Excessive Agency Cloud Demo (`lab_cloud_llm_model_excessive_agency()`)

Used for: only the excessive agency lab.

```
LAB_CLOUD_LLM_MODEL_EXCESSIVE_AGENCY
    ↓ if unset
LAB_CLOUD_LLM_MODEL
    ↓ if unset
GEMINI_MODEL
    ↓ if unset
OPENAI_MODEL
    ↓ if unset
"" (empty — cloud calls fail)
```

### Model Name Inference Rule

If the model value **contains a `/`**, it's passed to LiteLLM as-is
(e.g. `anthropic/claude-3-5-sonnet-...`).  
If it does **not** contain a `/`, the app assumes OpenAI and prefixes `openai/`
(e.g. `gpt-4o-mini` → `openai/gpt-4o-mini`).

## API Keys

| Variable | Provider | Format Check |
|----------|----------|-------------|
| `OPENAI_API_KEY` | OpenAI | Must start with `sk-` |
| `GEMINI_API_KEY` | Google Gemini | Must be ≥ 8 characters |
| `ANTHROPIC_API_KEY` | Anthropic | Must be ≥ 8 characters |

Keys can be set in two places (resolved by `get_openai_api_key()`):

1. **Session key** — entered by the user in Lab Setup UI
2. **Environment variable** — preconfigured on the server

Resolution order depends on two boolean env vars:

| Variable | Default | Effect |
|----------|---------|--------|
| `PREFER_SESSION_OPENAI_KEY` | `true` | Session key wins over env key |
| `ALLOW_PRECONFIGURED_OPENAI_KEY` | `true` | Fall back to env key if no session key |

## UI Override Variables

When using a non-OpenAI provider, the UI defaults to generic "LLM" labels.
Override them with these:

| Variable | Default Example |
|----------|----------------|
| `LLM_UI_PROVIDER_NAME` | `Google Gemini` |
| `LLM_UI_KEY_LABEL` | `Google AI API key:` |
| `LLM_UI_KEY_PLACEHOLDER` | `Enter your Google AI Studio API key` |
| `LLM_UI_DOCS_URL` | `https://aistudio.google.com/apikey` |
| `LLM_UI_DOCS_ANCHOR` | `Google AI Studio` |
| `LLM_UI_LAB_HEADING` | `Option 1: Google Gemini API (Paid)` |
| `LLM_UI_LAB_DESCRIPTION` | `Use Gemini models through Google's API...` |

## Docker & Workshop Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `DOCKER_CHALLENGES_PUBLIC_HOST` | **Yes** | — | Hostname/IP for spawned containers |
| `PWNZZAI_PUBLIC_HOST` | Optional | — | Alias for above |
| `CTFD_SECRET_KEY` | Optional | — | Production CTFd session key |
| `OLLAMA_PUBLISH` | Optional | `0.0.0.0:11434` | Ollama bind address |
| `COMPOSE_PROFILES` | Optional | — | Set to `local-ollama` to start bundled Ollama |
| `PWNZZAI_OLLAMA_GPU` | Optional | — | Set to `1` for NVIDIA GPU in workshop |

## Provider Selection

| Variable | Values | Default | Purpose |
|----------|--------|---------|---------|
| `MODEL_PROVIDER` | `auto`, `ollama`, `openai` | `auto` | Global provider preference |
| `ENABLE_PROVIDER_FALLBACK` | `true`, `false` | `true` | Fall back to Ollama when no API key |
| `OLLAMA_HOST` | URL | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | string | `llama3.2:1b` | Primary Ollama model |
| `OLLAMA_FALLBACK_MODEL` | string | `mistral:7b` | Secondary model |
| `MODEL_TIMEOUT_SECONDS` | int | `60` | LLM request timeout |

## Complete Variable List

See `.env.example` for the full list with inline descriptions. This doc
only covers variables with non-trivial interaction rules or precedence chains.
