# Workshop setup: choosing your cloud AI (OpenAI, Claude, Gemini, and more)

This guide is for **people running the workshop** (instructors or IT staff), not for participants typing in the browser.

The app can talk to different AI providers (OpenAI, Anthropic Claude, Google Gemini, and others supported by [LiteLLM](https://docs.litellm.ai/docs/providers)). You configure that **on the server** before participants open the lab.

---

## What you are doing (in plain terms)

1. You pick **which company’s AI** will answer the “cloud” demos (the ones that are not using free local Ollama).
2. You put **secret keys and settings** in a configuration file or hosting panel on the machine where the app runs.
3. You **restart** the app so it reads the new settings.
4. Participants still use **Lab Setup** in the browser to paste **their** key (unless you preconfigure a key on the server).

---

## Step 1 — Decide which AI provider to use

Pick **one** primary setup:

| If you want… | Typical choice | What participants need |
|--------------|----------------|-------------------------|
| OpenAI (GPT) models | OpenAI | An API key from OpenAI |
| Anthropic Claude | Anthropic | An API key from Anthropic |
| Google Gemini | Google AI (Gemini) | A Google AI Studio API key |

You can change later; just update the settings and restart again.

---

## Step 2 — Which model name is used (no hardcoded defaults in the app)

Cloud model IDs come **only from environment variables** (or from **`LITELLM_MODEL`** / **`GEMINI_MODEL`** / **`OPENAI_MODEL`** for fallbacks). Set at least one path below or cloud calls may get an empty model name.

**Per-lab overrides (optional):**

1. **`LAB_CLOUD_LLM_MODEL`** — **Most** cloud demos (prompt injection, insecure plugin, RAG, misinformation, DoS, order access, etc.).

2. **`LAB_CLOUD_LLM_MODEL_EXCESSIVE_AGENCY`** — **Excessive agency** cloud demo only. If unset, the app falls back to `LAB_CLOUD_LLM_MODEL`, then **`GEMINI_MODEL`**, then **`OPENAI_MODEL`**.

**If those are unset**, each resolves in order: **`GEMINI_MODEL`** (see Step 3) → bare **`OPENAI_MODEL`** (LiteLLM route `openai/...`).

You can set lab variables to a **full route** with a provider prefix, for example:

- `openai/gpt-4o-mini` — OpenAI
- `anthropic/claude-3-5-sonnet-20240620` — Anthropic Claude (example; check Anthropic’s current model list)
- `gemini/gemini-3.1-flash-lite` — Google Gemini (example; check Google’s current model list)

**Rule of thumb:** If the value contains a **`/`**, the app sends it to LiteLLM as-is. If it does **not** contain a **`/`**, the app assumes OpenAI and adds `openai/` in front (so `gpt-3.5-turbo` becomes `openai/gpt-3.5-turbo`).

---

## Step 3 — Global route: `LITELLM_MODEL` or `GEMINI_MODEL`

**`LITELLM_MODEL`** (optional) — Full LiteLLM route, e.g. `gemini/gemini-3.1-flash-lite`, `openai/gpt-4o-mini`. When set, it wins for the Lab Setup UI and for any code path that uses the “resolved” default model.

**`GEMINI_MODEL`** (optional) — Google model id **without** picking a default in code: either a **bare** id (e.g. `gemini-3.1-flash-lite`, turned into `gemini/gemini-3.1-flash-lite`) or a **full** `provider/model` string if you include a `/`.

Resolution order for the global default: **`LITELLM_MODEL`** → **`GEMINI_MODEL`** → **`OPENAI_MODEL`** → `openai/{OPENAI_MODEL}`.

For workshops, either set **`GEMINI_MODEL`** plus **`GEMINI_API_KEY`**, or set explicit **`LAB_CLOUD_*`** / **`LITELLM_MODEL`** as in the examples below.

---

## Step 4 — API keys (environment variables)

Each provider expects its key in the environment **on the server** (or in your Docker / hosting secrets):

| Provider | Typical environment variable |
|----------|------------------------------|
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Google Gemini | `GEMINI_API_KEY` or `GOOGLE_API_KEY` (see LiteLLM docs for the exact name for your model string) |

Participants can also paste a key in **Lab Setup** in the app; that key is sent with requests when they use the labs.

---

## Step 5 — Examples you can copy

### Example A — OpenAI for cloud labs

Set a bare OpenAI model name (the app prefixes `openai/`) and your key:

```bash
export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="gpt-4o-mini"
```

Optional explicit per-lab names:

```bash
export LAB_CLOUD_LLM_MODEL="gpt-3.5-turbo"
export LAB_CLOUD_LLM_MODEL_EXCESSIVE_AGENCY="gpt-4o-mini"
```

### Example B — Claude (Anthropic) for most labs, same for excessive agency

```bash
export LAB_CLOUD_LLM_MODEL="anthropic/claude-3-5-sonnet-20240620"
export LAB_CLOUD_LLM_MODEL_EXCESSIVE_AGENCY="anthropic/claude-3-5-sonnet-20240620"
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Example C — Google Gemini for most labs

Minimal (bare Gemini id; no model string hardcoded in the application):

```bash
export GEMINI_MODEL="gemini-3.1-flash-lite"
export GEMINI_API_KEY="your-google-ai-studio-key"
```

Equivalent explicit routes (optional):

```bash
export LITELLM_MODEL="gemini/gemini-3.1-flash-lite"
export LAB_CLOUD_LLM_MODEL="gemini/gemini-3.1-flash-lite"
export LAB_CLOUD_LLM_MODEL_EXCESSIVE_AGENCY="gemini/gemini-3.1-flash-lite"
export GEMINI_API_KEY="your-google-ai-studio-key"
```

### Example D — Mixed (advanced)

You can use Claude for most demos and a different model only for excessive agency:

```bash
export LAB_CLOUD_LLM_MODEL="anthropic/claude-3-5-sonnet-20240620"
export LAB_CLOUD_LLM_MODEL_EXCESSIVE_AGENCY="openai/gpt-4o-mini"
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

---

## Step 6 — Optional: labels in the browser

If you use a non-OpenAI provider, the app tries to show the right **names and links** in Lab Setup. You can override text with:

- `LLM_UI_PROVIDER_NAME`
- `LLM_UI_KEY_LABEL`
- `LLM_UI_DOCS_URL`
- and other `LLM_UI_*` variables listed in `.env.example`

---

## Step 7 — Apply and restart

1. Put the `export` lines (or the equivalent in Docker Compose, systemd, or your host panel) on the **same machine** that runs the Flask app.
2. **Restart** the application process (or container) so it loads the new environment.
3. Open the app, go to **Lab Setup**, and confirm the status line matches your provider.
4. Run through **one** short cloud demo (for example insecure plugin) before the workshop.

---

## If something fails

- **Wrong provider / wrong key type:** Check that the **model string** (`LAB_CLOUD_*`) matches the **company** of the key (Anthropic key for `anthropic/...`, etc.).
- **Model not found:** The exact string must match what LiteLLM and your provider support; copy it from the provider’s or LiteLLM’s documentation.
- **Still seeing “OpenAI” in the UI:** Set `LLM_UI_PROVIDER_NAME` or use a `gemini/` / `anthropic/` route so the built-in labels update; see `.env.example`.

For a full list of variables, see **[`.env.example`](../env.example)** in the project root.
