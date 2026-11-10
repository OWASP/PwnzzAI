# Getting Started

## Prerequisites

- Python 3.11+
- pip package manager
- (Optional) Docker for containerized development
- (Optional) Ollama for local LLM support

## Environment Setup

### 1. Virtual Environment

```bash
python -m venv venv
.\venv\Scripts\activate    # Windows
source venv/bin/activate   # Linux/macOS
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

For development, install lint tools:

```bash
pip install ruff
```

For documentation builds:

```bash
pip install mkdocs-material mkdocstrings mkdocstrings-python
```

### 3. Quick Start with Make

```bash
make venv              # Create virtual environment
make bootstrap-dev     # venv + pip upgrade + app/test deps + ruff
make dev               # Flask dev server on 0.0.0.0:8080
```

### 4. Configure Environment

```bash
cp .env.example .env   # Then edit .env as needed
```

## Running the App

### Option A: Source Code (no Docker)

```bash
make dev
# or: flask run --host=0.0.0.0 --port=8080
```

Open `http://localhost:8080`.

### Option B: Docker Compose

```bash
make compose-up        # PwnzzAI + Ollama
# or: docker compose up -d
```

### Option C: External Ollama

```bash
make compose-ext-up    # PwnzzAI only, uses existing Ollama
```

## Useful Make Targets

| Command | What it does |
|---------|-------------|
| `make test` | Run all tests |
| `make lint` | Run Ruff linter |
| `make check` | Lint + test |
| `make docs` | Build documentation site |
| `make docs-serve` | Preview docs with live reload |
| `make compose-up` | Start Docker stack |
| `make compose-down` | Stop Docker stack |

See the [Makefile](https://github.com/OWASP/PwnzzAI/blob/main/Makefile) for all 60+ targets.
