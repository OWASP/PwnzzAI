# PwnzzAI — one entrypoint for dev, Docker, tests, lint, QA, and workshop scripts.
# Run `make help` for a sorted list of targets. Most paths assume repo root (CURDIR).
# Quick start: `make venv && make bootstrap-dev` then `make check` (needs `make install-lint` or `pip install ruff` for lint).

.DEFAULT_GOAL := help

SHELL := /usr/bin/env bash

# --- configurable paths / images ---
VENV            ?= .venv
PYTHON          := $(VENV)/bin/python
PIP             := $(VENV)/bin/pip
COMPOSE         ?= docker compose
COMPOSE_FILE    ?= docker-compose.yml
COMPOSE_EXT     ?= docker-compose.external-ollama.yml
WORKSHOP_COMPOSE ?= deploy/docker-compose.workshop.yml
DEPLOY_DIR      ?= deploy
PWNZZAI_IMAGE   ?= ghcr.io/maryammouzarani2024/pwnzzai:latest
LOCAL_IMAGE     ?= pwnzzai-local:dev
TEST_IMAGE      ?= pwnzzai:test-ci
APP_PORT        ?= 8080
DOCS_SITE_DIR   ?= site
OLLAMA_MODEL    ?= llama3.2:1b

export FLASK_APP ?= main.py

.PHONY: help
help: ## List all Makefile targets with short descriptions
	@printf '%s\n' "PwnzzAI Makefile — common commands (see README.md, CONTRIBUTING.md, tests/README.md, scripts/ctfd_setup/README.md)"
	@grep -E '^[a-zA-Z0-9_.-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-40s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# Virtualenv & local Python (Option 3 / CONTRIBUTING)
# =============================================================================

.PHONY: venv
venv: ## Create $(VENV) (python3 -m venv)
	python3 -m venv "$(VENV)"

.PHONY: pip-upgrade
pip-upgrade: ## Upgrade pip inside $(VENV)
	"$(PYTHON)" -m pip install --upgrade pip

.PHONY: install
install: ## pip install -r requirements.txt (needs venv)
	"$(PYTHON)" -m pip install -r requirements.txt

.PHONY: install-dev
install-dev: ## pip install app + test requirements (CONTRIBUTING)
	"$(PYTHON)" -m pip install -r requirements.txt -r requirements-test.txt

.PHONY: install-lint
install-lint: ## Install Ruff in $(VENV) (same as CI lint workflow)
	"$(PYTHON)" -m pip install ruff

.PHONY: bootstrap-dev
bootstrap-dev: venv pip-upgrade install-dev install-lint ## venv + pip upgrade + app/test deps + ruff

.PHONY: install-system-deps
install-system-deps: ## Ubuntu/Debian: libzbar0 for tests (may need sudo)
	apt-get update && apt-get install -y libzbar0

.PHONY: install-host
install-host: ## Run install.sh (Ollama installer + pip + apt; needs review/sudo)
	bash ./install.sh

.PHONY: dev
dev: ## Flask dev server on 0.0.0.0:8080 (Ollama on host; set OLLAMA_HOST if needed)
	"$(PYTHON)" -m flask run --host=0.0.0.0 --port=$(APP_PORT)

.PHONY: dev-system-python
dev-system-python: ## flask run using system python3 (no venv)
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements.txt
	python3 -m flask run --host=0.0.0.0 --port=$(APP_PORT)

# =============================================================================
# Lint & tests (host)
# =============================================================================

.PHONY: lint
lint: ## Ruff check (matches .github/workflows/lint.yml); run make install-lint or: pip install ruff
	@if [ -x "$(VENV)/bin/ruff" ]; then "$(VENV)/bin/ruff" check . --ignore E402 --ignore F401 --ignore F841; \
	elif command -v ruff >/dev/null 2>&1; then ruff check . --ignore E402 --ignore F401 --ignore F841; \
	else printf '%s\n' "ruff not found. Run: make install-lint  (or: pip install ruff)" >&2; exit 1; fi

.PHONY: test
test: ## pytest -v (matches .github/workflows/test.yml)
	pytest -v

.PHONY: test-quiet
test-quiet: ## pytest (default verbosity)
	pytest

.PHONY: test-unit
test-unit: ## pytest tests/unit/
	pytest tests/unit/

.PHONY: test-integration
test-integration: ## pytest tests/integration/
	pytest tests/integration/

.PHONY: test-functional
test-functional: ## pytest tests/functional/
	pytest tests/functional/

.PHONY: test-security
test-security: ## pytest tests/security/ (no-op if directory missing; see tests/README.md)
	@if [ -d tests/security ]; then pytest tests/security/ -v; \
	else printf '%s\n' "tests/security/ not present — skipping."; fi

.PHONY: test-cov
test-cov: ## pytest with HTML + term coverage (tests/README.md)
	pytest --cov=application --cov-report=html --cov-report=term-missing

.PHONY: test-cov-xml
test-cov-xml: ## pytest with XML coverage (CI example in tests/README.md)
	pytest --cov=application --cov-report=xml

.PHONY: test-not-openai
test-not-openai: ## Skip tests marked openai (pytest.ini)
	pytest -m "not openai"

.PHONY: test-e2e-pytest
test-e2e-pytest: ## pytest tests/e2e/ (requires running app + Ollama if tests need them)
	pytest tests/e2e/ -v

.PHONY: check
check: lint test ## Lint then full pytest (local “CI”)

# =============================================================================
# Tests in Docker (no compose service — ephemeral container, CI-like deps)
# =============================================================================

.PHONY: test-docker-build
test-docker-build: ## Build $(TEST_IMAGE) from Dockerfile for test runs
	docker build -t "$(TEST_IMAGE)" .

.PHONY: test-docker
test-docker: test-docker-build ## Run pytest -v inside $(TEST_IMAGE) (installs requirements-test in container)
	docker run --rm -t "$(TEST_IMAGE)" \
		sh -lc 'python -m pip install -q -r requirements-test.txt && pytest -v'

.PHONY: test-docker-cov
test-docker-cov: test-docker-build ## pytest with coverage inside container
	docker run --rm -t "$(TEST_IMAGE)" \
		sh -lc 'python -m pip install -q -r requirements-test.txt && pytest --cov=application --cov-report=term-missing -v'

# =============================================================================
# Docker Compose — standard stack (README Option 1)
# =============================================================================

.PHONY: compose-config
compose-config: ## Validate docker-compose.yml
	$(COMPOSE) -f "$(COMPOSE_FILE)" config >/dev/null

.PHONY: compose-config-ext
compose-config-ext: ## Validate docker-compose.external-ollama.yml
	$(COMPOSE) -f "$(COMPOSE_EXT)" config >/dev/null

.PHONY: compose-up
compose-up: ## docker compose up -d (default PWNZZAI_IMAGE from compose file)
	PWNZZAI_IMAGE="$(PWNZZAI_IMAGE)" $(COMPOSE) -f "$(COMPOSE_FILE)" up -d

.PHONY: compose-down
compose-down: ## docker compose down
	PWNZZAI_IMAGE="$(PWNZZAI_IMAGE)" $(COMPOSE) -f "$(COMPOSE_FILE)" down

.PHONY: compose-down-volumes
compose-down-volumes: ## docker compose down -v (removes ollama_data)
	PWNZZAI_IMAGE="$(PWNZZAI_IMAGE)" $(COMPOSE) -f "$(COMPOSE_FILE)" down -v

.PHONY: compose-ps
compose-ps: ## docker compose ps
	$(COMPOSE) -f "$(COMPOSE_FILE)" ps

.PHONY: compose-logs-app
compose-logs-app: ## Tail app logs
	$(COMPOSE) -f "$(COMPOSE_FILE)" logs -f pwnzzai-app

.PHONY: compose-logs-ollama
compose-logs-ollama: ## Tail Ollama logs
	$(COMPOSE) -f "$(COMPOSE_FILE)" logs -f ollama

.PHONY: compose-build-local
compose-build-local: ## docker build local tag + compose up (README “build locally”)
	docker build -t "$(LOCAL_IMAGE)" .
	PWNZZAI_IMAGE="$(LOCAL_IMAGE)" $(COMPOSE) -f "$(COMPOSE_FILE)" up -d

.PHONY: compose-pull-model
compose-pull-model: ## docker exec ollama ollama pull $(OLLAMA_MODEL) (compose must be up)
	docker exec ollama ollama pull "$(OLLAMA_MODEL)"

# =============================================================================
# Docker Compose — external Ollama (README Option 2 + OLLAMA_CONNECTION_TROUBLESHOOTING)
# =============================================================================

.PHONY: compose-ext-up
compose-ext-up: ## External Ollama compose up (set OLLAMA_HOST before make if needed)
	PWNZZAI_IMAGE="$(PWNZZAI_IMAGE)" $(COMPOSE) -f "$(COMPOSE_EXT)" up -d

.PHONY: compose-ext-up-recreate
compose-ext-up-recreate: ## Force recreate external stack (troubleshooting doc)
	PWNZZAI_IMAGE="$(PWNZZAI_IMAGE)" $(COMPOSE) -f "$(COMPOSE_EXT)" up -d --force-recreate

.PHONY: compose-ext-down
compose-ext-down: ## External Ollama compose down
	PWNZZAI_IMAGE="$(PWNZZAI_IMAGE)" $(COMPOSE) -f "$(COMPOSE_EXT)" down

.PHONY: compose-ext-down-orphans
compose-ext-down-orphans: ## External compose down with --remove-orphans (OLLAMA troubleshooting)
	PWNZZAI_IMAGE="$(PWNZZAI_IMAGE)" $(COMPOSE) -f "$(COMPOSE_EXT)" down --remove-orphans

.PHONY: compose-ext-logs
compose-ext-logs: ## Tail app logs (external compose)
	$(COMPOSE) -f "$(COMPOSE_EXT)" logs -f pwnzzai-app

.PHONY: compose-ext-logs-tail
compose-ext-logs-tail: ## Last 120 lines of app logs (troubleshooting doc)
	$(COMPOSE) -f "$(COMPOSE_EXT)" logs --tail=120 pwnzzai-app

.PHONY: compose-probe-ollama
compose-probe-ollama: ## Exec into app container: GET Ollama /api/tags via Python (needs running pwnzzai-shop)
	docker exec pwnzzai-shop python -c "import requests; print(requests.get('http://host.docker.internal:11434/api/tags', timeout=5).text)"

.PHONY: compose-inspect-app
compose-inspect-app: ## docker inspect image and OLLAMA_HOST env (troubleshooting doc)
	@docker inspect pwnzzai-shop --format '{{.Config.Image}} {{.Image}}' 2>/dev/null || true
	@docker inspect pwnzzai-shop --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | grep OLLAMA_HOST || true

# =============================================================================
# Docker image build (CI / README)
# =============================================================================

.PHONY: docker-build
docker-build: ## docker build -t $(LOCAL_IMAGE) .
	docker build -t "$(LOCAL_IMAGE)" .

.PHONY: docker-build-no-cache
docker-build-no-cache: ## docker build --no-cache --pull (OLLAMA troubleshooting)
	docker build --no-cache --pull -t "$(LOCAL_IMAGE)" .

.PHONY: docker-login-ghcr
docker-login-ghcr: ## docker login ghcr.io (registry auth; run interactively)
	docker login ghcr.io

# =============================================================================
# QA & smoke scripts (scripts/, tests/README.md, CONTRIBUTING)
# =============================================================================

.PHONY: smoke-docker
smoke-docker: ## scripts/docker-smoke-test.sh (optional APP_IMAGE=…)
	bash scripts/docker-smoke-test.sh

.PHONY: e2e-challenge-solve
e2e-challenge-solve: ## E2E solvability harness (needs .venv + Docker; see tests/README.md)
	bash scripts/qa/run-challenge-solve-e2e.sh

.PHONY: e2e
e2e: e2e-challenge-solve ## Alias for e2e-challenge-solve

.PHONY: qa-scanner-probe
qa-scanner-probe: ## HTTP 200 smoke on key paths (optional APP_BASE=http://127.0.0.1:8080)
	bash scripts/qa/scanner-probe-smoke.sh

.PHONY: qa-integration-gates
qa-integration-gates: ## Model + unit + CTFd gates (scripts/qa/run-model-integration-gates.sh)
	bash scripts/qa/run-model-integration-gates.sh

.PHONY: qa-load-test
qa-load-test: ## Shared-model load test (USERS TIMEOUT_SECONDS APP_URL)
	bash scripts/qa/load-test-shared-model.sh

# =============================================================================
# CTFd workshop (scripts/ctfd_setup/README.md)
# =============================================================================

.PHONY: ctfd-env-example
ctfd-env-example: ## cp .env.example .env (workshop prep)
	@test -f .env && echo ".env already exists; skip" || cp .env.example .env

.PHONY: ctfd-bootstrap
ctfd-bootstrap: ## scripts/ctfd_setup/setup-model-and-ctfd.sh (Step 1 workshop)
	bash scripts/ctfd_setup/setup-model-and-ctfd.sh

.PHONY: ctfd-bootstrap-alt
ctfd-bootstrap-alt: ## scripts/ctfd_setup/bootstrap-ctfd-workshop.sh
	bash scripts/ctfd_setup/bootstrap-ctfd-workshop.sh

.PHONY: ctfd-redeploy
ctfd-redeploy: ## Rebuild/restart CTFd only (scripts/ctfd_setup/redeploy-ctfd-workshop.sh)
	bash scripts/ctfd_setup/redeploy-ctfd-workshop.sh

.PHONY: ctfd-teardown
ctfd-teardown: ## scripts/ctfd_setup/teardown-ctfd-workshop.sh (pass ARGS="--volumes" etc.)
	bash scripts/ctfd_setup/teardown-ctfd-workshop.sh $(ARGS)

.PHONY: ctfd-register-challenge
ctfd-register-challenge: ## Step 2: register challenge (needs CTFD_API_TOKEN / .env)
	bash scripts/ctfd_setup/register-pwnzzai-challenge.sh

.PHONY: ctfd-setup-on-ctfd
ctfd-setup-on-ctfd: ## Preferred Step 2 wrapper (scripts/ctfd_setup/setup-pwnzzai-on-ctfd.sh)
	bash scripts/ctfd_setup/setup-pwnzzai-on-ctfd.sh

.PHONY: ctfd-reregister-challenge
ctfd-reregister-challenge: ## Delete + recreate challenge (scripts/ctfd_setup/reregister-pwnzzai-challenge.sh)
	bash scripts/ctfd_setup/reregister-pwnzzai-challenge.sh

.PHONY: workshop-ps
workshop-ps: ## docker compose -f deploy/docker-compose.workshop.yml ps
	$(COMPOSE) -f "$(WORKSHOP_COMPOSE)" ps

.PHONY: workshop-logs-ctfd
workshop-logs-ctfd: ## Tail CTFd logs (troubleshooting)
	$(COMPOSE) -f "$(WORKSHOP_COMPOSE)" logs -f ctfd

.PHONY: workshop-build-ctfd
workshop-build-ctfd: ## Rebuild ctfd service image (troubleshooting)
	$(COMPOSE) -f "$(WORKSHOP_COMPOSE)" build ctfd

.PHONY: workshop-up-ctfd
workshop-up-ctfd: ## Recreate ctfd after build (troubleshooting)
	$(COMPOSE) -f "$(WORKSHOP_COMPOSE)" up -d --force-recreate ctfd

.PHONY: workshop-socket-proxy-recreate
workshop-socket-proxy-recreate: ## Recreate docker-socket-proxy (troubleshooting)
	$(COMPOSE) -f "$(WORKSHOP_COMPOSE)" up -d --force-recreate docker-socket-proxy

.PHONY: workshop-build-pwnzzai-image
workshop-build-pwnzzai-image: ## docker build workshop Flask image (scripts/ctfd_setup README)
	docker build -f "$(DEPLOY_DIR)/Dockerfile.pwnzzai-workshop" -t pwnzzai-workshop:latest .

.PHONY: workshop-debug-docker
workshop-debug-docker: ## deploy/debug-ctfd-docker.sh (from deploy/)
	bash "$(DEPLOY_DIR)/debug-ctfd-docker.sh"

.PHONY: do-bootstrap
do-bootstrap: ## DigitalOcean / cloud workshop bootstrap (needs root — sudo make do-bootstrap)
	bash scripts/bootstrap-digitalocean-workshop.sh

.PHONY: do-cleanup
do-cleanup: ## Workshop cleanup on droplet (ARGS="--volumes"; often sudo)
	bash scripts/bootstrap-digitalocean-workshop.sh --cleanup $(ARGS)

# =============================================================================
# Register helpers (direct Python — scripts/ctfd_setup README)
# =============================================================================

.PHONY: register-challenge-py
register-challenge-py: ## python3 deploy/register_pwnzzai_challenge.py (env from .env)
	python3 deploy/register_pwnzzai_challenge.py

.PHONY: reregister-challenge-py
reregister-challenge-py: ## python3 deploy/reregister_pwnzzai_challenge.py
	python3 deploy/reregister_pwnzzai_challenge.py

# =============================================================================
# Documentation (MkDocs)
# =============================================================================

.PHONY: sync-docs
sync-docs: ## Copy canonical files into docs/ before build (single source of truth)
	python3 scripts/sync-docs.py

.PHONY: docs
docs: sync-docs ## Build MkDocs site (runs sync-docs first)
	mkdocs build --site-dir $(DOCS_SITE_DIR)

.PHONY: docs-serve
docs-serve: sync-docs ## Serve MkDocs locally with live reload (runs sync-docs first)
	mkdocs serve

# =============================================================================
# Documentation Quality (local)
# =============================================================================

.PHONY: install-docs-qa
install-docs-qa: ## Install doc quality tools (pytest-codeblocks)
	"$(PYTHON)" -m pip install pytest-codeblocks

.PHONY: check-codeblocks
check-codeblocks: ## Validate Python code blocks in documentation (scripts/check-codeblocks.py)
	python3 scripts/check-codeblocks.py

.PHONY: check-doc-coverage
check-doc-coverage: ## Check all routes and vulnerability modules are documented (scripts/check-doc-coverage.py)
	python3 scripts/check-doc-coverage.py

.PHONY: check-links
check-links: ## Check external links in markdown (requires lychee, or runs in CI)
	@if command -v lychee >/dev/null 2>&1; then lychee --config lychee.toml .; \
	else printf '%s\n' "lychee not found. Install: cargo install lychee, or let CI run this check." >&2; fi

.PHONY: check-spelling
check-spelling: ## Spell-check docs (requires cspell, or runs in CI)
	@if command -v cspell >/dev/null 2>&1; then cspell --config cspell.json "**/*.md" --no-summary; \
	else printf '%s\n' "cspell not found. Install: npm install -g cspell, or let CI run this check." >&2; fi

.PHONY: check-markdown
check-markdown: ## Lint markdown style (requires markdownlint-cli2, or runs in CI)
	@if command -v markdownlint-cli2 >/dev/null 2>&1; then markdownlint-cli2 "**/*.md" "#venv" "#.venv" "#node_modules" "#site" "#docs/tmp"; \
	else printf '%s\n' "markdownlint-cli2 not found. Install: npm install -g markdownlint-cli2, or let CI run this check." >&2; fi

.PHONY: check-docs
check-docs: check-markdown check-links check-spelling check-codeblocks check-doc-coverage ## Run all doc quality checks (best-effort locally, authoritative in CI)
