# Documentation Standards

How to contribute new or updated documentation.

## Single Source of Truth

Content lives in **one place**. The `scripts/sync-docs.py` script copies
canonical root files into `docs/` before every MkDocs build.

| Canonical file | Synced to `docs/` | Edit this file |
|---|---|---|
| `README.md` | `docs/README.md` | Root `README.md` |
| `CONTRIBUTING.md` | `docs/community/contributing.md` | Root `CONTRIBUTING.md` |
| `OLLAMA_CONNECTION_TROUBLESHOOTING.md` | `docs/ops/troubleshooting.md` | Root `OLLAMA_CONNECTION_TROUBLESHOOTING.md` |
| `tests/README.md` | `docs/quality-assurance/testing-guide.md` | Root `tests/README.md` |
| `.env.example` | `docs/env.example` | Root `.env.example` |

**Never edit the copies in `docs/`** — they are overwritten on every build.

## File Organization

```
docs/
├── README.md                       # Landing page (synced from root)
├── architecture/
│   ├── overview.md                 # High-level system design
│   ├── data-flow.md                # Request lifecycle, provider resolution
│   └── threat-model.md             # OWASP Top 10 mapping
├── developer/
│   ├── getting-started.md          # Environment setup
│   ├── codebase-map.md             # Directory structure, module roles
│   ├── api-reference.md            # All endpoints
│   ├── api-modules.md              # Auto-generated (mkdocstrings)
│   └── adding-features.md          # Vulnerability recipe, coding conventions
├── labs/
│   ├── overview.md                 # Platform navigation
│   ├── lab-format.md               # Escalation ladder, lab structure
│   └── scenario-list.md            # Challenge walkthroughs
├── quality-assurance/
│   ├── testing-guide.md            # Test suite (synced from tests/README.md)
│   └── security-checks.md          # Vulnerability verification checklist
├── ops/
│   ├── docker-orchestration.md     # Compose files, networking
│   ├── env-variables.md            # All .env parameters
│   ├── cloud-setup.md              # Cloud LLM provider setup
│   └── troubleshooting.md          # Known issues (synced from root)
├── security/
│   ├── disclosure.md               # Responsible disclosure policy
│   ├── usage-policy.md             # Educational use disclaimer
│   └── data-privacy.md             # Session/data handling notes
├── community/
│   ├── contributing.md             # PR process (synced from root)
│   └── doc-standards.md            # This file
└── releases/
    ├── CHANGELOG.md                # Version history
    └── ROADMAP.md                  # Future goals
```

## Documentation Checklist

Every PR that changes code must be checked against this list:

| What changed | Update |
|---|---|
| New route/endpoint | Add to `docs/developer/api-reference.md` |
| New vulnerability module | Add to `docs/developer/codebase-map.md` module table |
| New env var | Add to `.env.example` + `docs/ops/env-variables.md` |
| Changed dependency | Update `docs/architecture/overview.md` |
| New prompt template in `prompts/` | Update `docs/labs/lab-format.md` |
| New Docker/deploy script | Update `docs/ops/docker-orchestration.md` |
| API response changed | Update entry in `docs/developer/api-reference.md` |
| New Makefile target | Add `## description` in Makefile |
| **New or changed docs** | Run `make check-codeblocks` and `make docs` before pushing

### Automated Coverage Check

A static analysis script (`scripts/check-doc-coverage.py`) runs in CI on every
PR that touches code or docs. It uses `ast` to parse `application/route.py`
route decorators and compares them against `docs/developer/api-reference.md`,
then checks every file in `application/vulnerabilities/` against
`docs/developer/codebase-map.md`. Any undocumented route or module fails the
build.

What it catches:

- **New endpoints** without a corresponding entry in the API reference
- **New vulnerability modules** without an entry in the codebase map
- **Route parameter mismatches** between the code and docs

Run it locally before pushing:

```bash
python scripts/check-doc-coverage.py
```

This is part of the `make check-docs` pipeline and runs alongside the other
four doc quality checks in CI.

## Documenting New Features

When adding a new vulnerability lab, create or update:

1. **Vulnerability module** in `application/vulnerabilities/` with docstrings
2. **Routes** in `application/route.py` with docstrings
3. **Template** in `application/templates/`
4. **Tests** in `tests/`
5. **Codebase map** — add to `docs/developer/codebase-map.md` module table
6. **Threat model** — add to `docs/architecture/threat-model.md` mapping table
7. **API reference** — add to `docs/developer/api-reference.md` with request/response
8. **Scenario list** — add to `docs/labs/scenario-list.md` if it's a challenge
9. **Security checks** — add to `docs/quality-assurance/security-checks.md`

## Documentation Build

```bash
make docs          # sync + mkdocs build
make docs-serve    # sync + mkdocs serve (live reload at localhost:8000)
```

The build runs `scripts/sync-docs.py` first, which copies canonical root files
into `docs/` with path rewriting, then builds the static site to `site/`.

## Quality Checks (CI)

Four automated checks run on every PR that touches documentation (via
`.github/workflows/docs-quality.yml`):

| Check | Tool | What it catches |
|---|---|---|
| Markdown style | `markdownlint-cli2` | Wrong heading nesting, broken list indentation, missing blank lines |
| Dead links | `lychee` | Broken URLs (404s, DNS failures, moved pages) |
| Spelling | `cspell` | Typos in prose, inconsistent casing of technical terms |
| Code snippets | `scripts/check-codeblocks.py` | Python code blocks with syntax errors |

### Running Locally

The code block checker is a Python script that works on any platform with no
extra dependencies:

```bash
make check-codeblocks
# or: python3 scripts/check-codeblocks.py
```

The doc coverage script also runs with stdlib only:

```bash
python scripts/check-doc-coverage.py
```

The other three tools (`markdownlint-cli2`, `lychee`, `cspell`) are Node.js/Rust
tools that are best run in CI. On the Makefile, they print a helpful message if
not installed locally:

```bash
make check-docs   # runs all 5 with graceful fallbacks
```

### Before Opening a PR

Run `make docs` to confirm the site builds without errors, then check:

- [ ] `make check-codeblocks` passes (no broken Python snippets)
- [ ] `python scripts/check-doc-coverage.py` passes (all routes and modules documented)
- [ ] New pages are linked from the nav or an existing page
- [ ] All relative links resolve correctly
