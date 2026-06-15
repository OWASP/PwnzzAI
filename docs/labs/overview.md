# Labs Overview

How to navigate the PwnzzAI Shop learning platform.

## Platform Navigation

The app has two types of pages:

- **Pizza Shop** — `/`, `/pizza/<id>`, `/orders`, `/login` — a working (but intentionally
  vulnerable) pizza ordering website
- **Lab Pages** — vulnerability demonstration pages accessible from the navigation bar

### User Accounts

| Username | Password | Role |
|----------|----------|------|
| `alice` | `alice` | Regular user |
| `bob` | `bob` | Regular user |

Some labs require login. Others work without authentication.

### Lab Setup

Before running cloud-backed labs, configure your API key:

1. Go to the **Basics** page
2. In **Lab Setup**, paste your API key (OpenAI/Gemini/Claude)
3. The UI updates to show your configured provider

For local labs, run **Setup Ollama** from the Basics page to pull models.

## Lab Format

Each lab page follows this structure:

```html
<div class="lab-container">
  <!-- Description of the vulnerability -->
  <!-- Ollama tab (local model) -->
  <!-- Cloud tab (requires API key) -->
  <!-- Explanation + mitigation -->
</div>
```

The `llm_ui` template context automatically adjusts labels, names, and
documentation links based on the configured cloud provider.

## Provider Tabs

Most labs offer two tabs:

| Tab | Backend | Requires |
|-----|---------|----------|
| **Ollama** | Local model via Ollama | Running Ollama with pulled model |
| **Cloud** | LiteLLM (OpenAI/Gemini/Claude) | API key in session + model configured |

The provider is resolved per-request via `resolve_provider()`. If no API key
is available, the app falls back to Ollama.

## Lab Index

See [scenario-list.md](scenario-list.md) for a complete list of available challenges.
