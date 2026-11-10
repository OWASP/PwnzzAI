# PwnzzAI Documentation

<img src="index.png" alt="PwnzzAI Shop" width="140" align="right">

PwnzzAI is an open-source, hands-on security education platform built and
maintained in partnership with the **[OWASP AI Exchange](https://owaspai.org/)**.
Delivered as an intentionally vulnerable pizza shop web application, it provides
practical, interactive demonstrations of LLM vulnerabilities across the OWASP
Top 10 for LLM Applications and AI Exchange threat taxonomy.

The platform supports dual-provider execution — local models via Ollama and
cloud models via LiteLLM (OpenAI, Gemini, Claude) — making it suitable for
both self-paced learning and instructor-led workshops.

---

## Getting Started

| Guide | Description |
|-------|-------------|
| [Deploy with Docker](ops/docker-orchestration.md) | Run PwnzzAI and Ollama in containers |
| [Run from Source](developer/getting-started.md) | Python virtual environment setup |
| [Cloud LLM Configuration](ops/cloud-setup.md) | Connect OpenAI, Gemini, or Claude |
| [Environment Variables](ops/env-variables.md) | Full configuration reference |

---

## Lab Catalog

| Guide | Description |
|-------|-------------|
| [Platform Overview](labs/overview.md) | Navigation, accounts, and provider tabs |
| [Lab Index](labs/scenario-list.md) | All 16 labs with page URLs and API endpoints |
| [Escalation Ladder](labs/lab-format.md) | B0–B9 direct prompt injection stages |

---

## Developer Resources

| Guide | Description |
|-------|-------------|
| [Getting Started](developer/getting-started.md) | Development environment and conventions |
| [Codebase Map](developer/codebase-map.md) | Module layout and directory structure |
| [Adding Features](developer/adding-features.md) | How to contribute a new vulnerability |
| [API Reference](developer/api-reference.md) | Complete endpoint documentation |
| [API Modules](developer/api-modules.md) | Python module reference |

---

## Architecture

| Guide | Description |
|-------|-------------|
| [System Overview](architecture/overview.md) | Stack, dependencies, and request lifecycle |
| [Data Flow](architecture/data-flow.md) | Provider resolution and detection pipelines |
| [Threat Model](architecture/threat-model.md) | Risk coverage mapped to OWASP categories |

---

## Quality & Operations

| Guide | Description |
|-------|-------------|
| [Testing Guide](quality-assurance/testing-guide.md) | Test suite structure and CI integration |
| [Security Checks](quality-assurance/security-checks.md) | Per-lab verification procedures |
| [Docker Orchestration](ops/docker-orchestration.md) | Compose architecture and networking |
| [Troubleshooting](ops/troubleshooting.md) | Common issues and fixes |

---

## Contributing & Policies

| Guide | Description |
|-------|-------------|
| [Contributing](community/contributing.md) | PR workflow, coding standards, and issue reporting |
| [Documentation Standards](community/doc-standards.md) | Doc conventions and sync rules |
| [Responsible Disclosure](security/disclosure.md) | How to report security issues |
| [Usage Policy](security/usage-policy.md) | Acceptable use and disclaimers |
| [Data Privacy](security/data-privacy.md) | Session handling and data isolation |

---

## Releases

| Guide | Description |
|-------|-------------|
| [Changelog](releases/CHANGELOG.md) | Version history |
| [Roadmap](releases/ROADMAP.md) | Planned features and milestones |

---

!!! warning "Educational Purpose Only"
    This application contains intentional security vulnerabilities designed for
    learning. Do not deploy in production, expose to untrusted networks, or
    store real user data.
