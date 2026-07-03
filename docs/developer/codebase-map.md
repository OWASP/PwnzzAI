# Codebase Map

## Directory Structure

```
D:\PwnzzAI\
├── application/              # Core Flask application
│   ├── __init__.py           # Flask app factory, DB init, context processor
│   ├── route.py              # All HTTP routes (~2100 lines, main controller)
│   ├── model.py              # SQLAlchemy models (Pizza, User, Comment, Order, RoutingFlag)
│   ├── llm_chat.py           # LiteLLM abstraction (chat_completion, tool calls)
│   ├── provider_config.py    # LLM provider resolution, env vars, UI strings
│   ├── ollama_setup.py       # Ollama lifecycle (start, check, pull models)
│   ├── sentiment_model.py    # scikit-learn LogisticRegression model
│   ├── static/               # CSS + images
│   ├── templates/            # 22 Jinja2 HTML templates
│   ├── prompts/              # Jinja2 prompt template helpers
│   │   ├── __init__.py
│   │   └── b_stream.py       # B0-B9 escalation ladder rendering
│   └── vulnerabilities/      # 24 vulnerability module files
│       ├── catering_rag_lab.py
│       ├── catering_sql_tool_lab.py
│       ├── data_poisoning.py
│       ├── direct_prompt_escalation.py
│       ├── model_theft.py
│       ├── ollama_*.py       # 9 Ollama-backed modules
│       ├── openai_*.py       # 9 OpenAI/LiteLLM-backed modules
│       ├── promotion_indirect_injection.py
│       ├── supply_chain.py
│       └── toxicity_support_lab.py
├── docs/                     # MkDocs documentation site
├── deploy/                   # Workshop deployment files (Docker, CTFd)
├── scripts/                  # Operational scripts (QA, CTFd, bootstrap)
├── tests/                    # pytest suite (~220 tests)
│   ├── unit/
│   ├── integration/
│   ├── functional/
│   └── e2e/
├── prompts/                  # Jinja2 prompt templates for escalation ladder
│   └── direct_prompt_escalation/
│       ├── b00.jinja2 ... b09.jinja2
├── .github/workflows/        # CI/CD: lint, test, docs, docker
├── mkdocs.yml                # Documentation site config
├── config.py                 # Flask config
├── main.py                   # Entry point
├── Makefile                  # 60+ targets
├── requirements.txt
├── requirements-test.txt
├── pyproject.toml            # Ruff linter config
├── pytest.ini                # Pytest markers
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Module Roles

### Core Application (`application/`)

| File | Role |
|------|------|
| `__init__.py` | Creates Flask app, initializes SQLAlchemy, registers context processor and routes |
| `route.py` | All HTTP routes — auth, pizza shop CRUD, lab endpoints, API handlers |
| `model.py` | 5 SQLAlchemy models: Pizza, User, Comment, Order, RoutingFlag |
| `llm_chat.py` | Provider-agnostic LLM calls via LiteLLM (`chat_completion()`, `completion_with_tools()`) |
| `provider_config.py` | Reads env vars, resolves LLM provider, provides UI strings |
| `ollama_setup.py` | Starts Ollama, checks status, pulls models |
| `sentiment_model.py` | scikit-learn LogisticRegression trained on pizza comments |

### Vulnerability Modules (`application/vulnerabilities/`)

Each vulnerability has a **page route** (GET, renders a template) and one or more
**API routes** (POST, returns JSON). See [api-reference.md](api-reference.md)
for the full endpoint list.

| Module | Vulnerability | OWASP LLM Top 10 |
|--------|-------------|-------------------|
| `ollama_direct_prompt_injection.py` | Direct Prompt Injection | LLM-01 |
| `openai_direct_prompt_injection.py` | Direct Prompt Injection (cloud) | LLM-01 |
| `ollama_indirect_prompt_injection.py` | Indirect Prompt Injection (QR) | LLM-01 |
| `openai_indirect_prompt_injection.py` | Indirect Prompt Injection (cloud) | LLM-01 |
| `direct_prompt_escalation.py` | B0-B9 Escalation Ladder | LLM-01 |
| `promotion_indirect_injection.py` | Promotion Photo Injection | LLM-01 |
| `ollama_sensitive_data_leakage.py` | Sensitive Info Disclosure | LLM-02 |
| `openai_sensitive_data_leakage.py` | Sensitive Info Disclosure (cloud) | LLM-02 |
| `supply_chain.py` | Supply Chain (malicious pickle) | LLM-03 |
| `data_poisoning.py` | Data & Model Poisoning | LLM-04 |
| `catering_rag_lab.py` | RAG Poisoning | LLM-04/LLM-08 |
| `ollama_excessive_agency.py` | Excessive Agency | LLM-06 |
| `openai_excessive_agency.py` | Excessive Agency (cloud) | LLM-06 |
| `ollama_misinformation.py` | Misinformation | LLM-09 |
| `openai_misinformation.py` | Misinformation (cloud) | LLM-09 |
| `ollama_dos.py` | Unbounded Consumption (DoS) | LLM-10 |
| `openai_dos.py` | Unbounded Consumption (cloud) | LLM-10 |
| `model_theft.py` | Model Theft | Legacy |
| `ollama_insecure_plugin.py` | Insecure Plugin | — |
| `openai_insecure_plugin.py` | Insecure Plugin (cloud) | — |
| `ollama_order_access.py` | Order Access (broken access) | — |
| `openai_order_access.py` | Order Access (cloud) | — |
| `catering_sql_tool_lab.py` | Agentic SQL Tool Routing | — |
| `toxicity_support_lab.py` | Toxicity/Support Safety | — |
