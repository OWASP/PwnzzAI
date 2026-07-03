# Changelog

All notable changes to PwnzzAI are documented here.

## [Unreleased]

### Added
- Full MkDocs documentation site with Mermaid diagrams, mkdocstrings, organized category structure
- `scripts/sync-docs.py` — single-source-of-truth sync for canonical docs
- `scripts/check-codeblocks.py` — validate Python code blocks in Markdown
- `scripts/check-doc-coverage.py` — AST-based validation that all routes and vulnerability modules are documented
- GitHub Pages deployment workflow (`.github/workflows/docs.yml`)
- Documentation quality CI pipeline (`.github/workflows/docs-quality.yml`)
- Archirecture docs: overview, data-flow, threat-model
- Developer docs: codebase-map, API reference, API modules, adding-features
- Lab docs: overview, lab-format, scenario-list
- Operations docs: docker-orchestration, env-variables, cloud-setup, troubleshooting
- Security policy docs: disclosure, usage-policy, data-privacy
- Community docs: contributing, doc-standards
- Release docs: ROADMAP

### Fixed
- Broken link in root README to `docs/workshop-cloud-llm-setup.md` → corrected to `ops/cloud-setup.md`
- Truncated CONTRIBUTING.md — added missing Coding Standards, Submitting Changes, Reporting Issues, Security Considerations sections
- References to non-existent `tests/security/` directory in testing-guide.md
- Missing contact email and disclosure timeline in security/disclosure.md
- Typo in CONTRIBUTING.md — "soutions" → "solutions"

### Removed
- Obsolete `docs/CHALLENGE_SOLUTIONS.md` (replaced by `labs/scenario-list.md`)
- Obsolete `docs/workshop-cloud-llm-setup.md` (migrated to `ops/cloud-setup.md`)

## [Workshop Release] — 2025-10

### Added
- CTFd workshop deployment, bootstrap scripts, and operator documentation (#85, #86)
- Docker Compose profiles for local and external Ollama modes (#90)
- LiteLLM support for multi-provider cloud labs (OpenAI, Anthropic, Gemini) (#90)
- Direct Prompt Injection escalation ladder (B0–B9) with 10 Jinja2 prompt templates (#90)
- RFC-EX-B: functional tests with mocked LLM backends for direct injection (#90)
- Corporate Catering RAG poisoning lab with TF-IDF retrieval (#90)
- Catering SQL Tool agentic abuse lab (F0–F4) (#90)
- Promotion Photo indirect injection lab (#90)
- Customer Support toxicity/guardrail evasion lab (#90)
- E2E challenge solvability harness with retry logic (#90)
- Test fixtures and mock infrastructure for CI-safe testing (#90)
- Provider configuration module with auto-detection (`resolve_provider()`) (#90)

## [CTFd Integration] — 2025-09

### Added
- CTFd challenge deployment scripts (#85)
- DigitalOcean bootstrap scripts for workshop operators (#85)
- QR code lab improvements with updated secret keys (#87, #88, #89)

## [Docker & Polish] — 2025-08

### Added
- Docker build pipeline and image publishing workflows (#33, #34, #35)
- Docker Compose configuration for local development (#39, #40)
- Multi-stage Dockerfile with model pre-loading support (#43, #44)

### Changed
- Removed model pre-loading from Docker image to reduce size (#45)
- Refined README for features, vulnerabilities, and project structure clarity (#61–77)

## [Core Lab Implementation] — 2025-06

### Added
- Direct Prompt Injection — 5 levels with escalating refusal guardrails
- Indirect Prompt Injection — QR code upload with 5 levels
- Insecure Plugin Design — SQL injection via LLM function calling
- Excessive Agency — automatic order placement without confirmation
- Sensitive Information Disclosure — RAG-based PII leakage
- Misinformation / Hallucination — forced fabrication via system prompt
- Denial of Service — simulated exponential degradation
- Model Theft — weight approximation via public inference API
- Data Poisoning — mislabeled training data contamination
- Supply Chain — malicious pickled model with XSS and RCE
- MIT License and GNU GPL v3 (#47)
- Sentiment model training pipeline from database comments

### Changed
- Rebranded from Pwnzza to PwnzzAI (#27)
- Restructured application module layout (routes, vulnerabilities, provider config)

## [Initial Prototype] — 2025-04

### Added
- Initial commit of DVLLM — Vulnerable Pizza Shop (#65be73d)
- Flask application skeleton with pizza shop UI
- Insecure plugin design — function calling with SQL injection (#c11a1b6)
- Model theft demonstration (#be9343e)
- Data poisoning workflow (#e722eae)
- Basic authentication with Alice and Bob user accounts
- SQLite database with Pizza, Comment, User, Order models
- Jitser-style UI templates
