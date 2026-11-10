# Contributing to PwnzzAI Shop

Thank you for your interest in contributing to PwnzzAI Shop! This project aims to educate developers about LLM security vulnerabilities through practical, hands-on examples. We welcome contributions that enhance the educational value and quality of this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
   - [Docker Smoke Tests](#docker-smoke-tests)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Security Considerations](#security-considerations)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Be kind, professional, and considerate in all interactions.

## Ways to Contribute

You can contribute to PwnzzAI Shop in several ways:

- **Bug Fixes**: Fix issues or improve existing functionality
- **New Vulnerabilities**: Add demonstrations of additional LLM vulnerabilities
- **Documentation**: Improve explanations, tutorials, or documentation
- **Test Coverage**: Add or improve test cases
- **Security Mitigations**: Enhance security solutions in the mitigation strategies sections
- **Model Support**: Add support for additional LLM models
- **UI/UX Improvements**: Enhance the user interface or user experience
- **Code Quality**: Refactor code for better maintainability

## Getting Started

1. **Fork the Repository**: Click the **Fork** button on the canonical repo: [https://github.com/OWASP/PwnzzAI](https://github.com/OWASP/PwnzzAI)

2. **Clone Your Fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/PwnzzAI.git
   cd PwnzzAI
   ```

3. **Add Upstream Remote** (track the canonical OWASP project):
   ```bash
   git remote add upstream https://github.com/OWASP/PwnzzAI.git
   ```

   If your GitHub fork still shows the **old parent repository**, GitHub will not let you open a pull request into **OWASP/PwnzzAI** from that fork. Fix it by **forking again from [OWASP/PwnzzAI](https://github.com/OWASP/PwnzzAI)** (or asking an org admin to **re-parent** your existing fork), then add a second remote (for example `origin` → your fork, `upstream` → OWASP) and push your topic branch there before opening the PR.

4. **Create a Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip package manager
- (Optional) Docker for containerized development

### Local Setup

1. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

3. **Install System Dependencies** (if needed for testing):
   ```bash
   sudo apt-get update
   sudo apt-get install -y libzbar0
   ```.

4. **Configure Environment**:
   - Copy `.flaskenv` if needed

## Testing

Before opening a PR, run tests locally:

```bash
pytest -v
```

### Docker Smoke Tests

Use the Docker smoke test routine before pushing to GitHub. It validates local Docker build and both Docker runtime modes.

1. Run the smoke test script:

```bash
./scripts/docker-smoke-test.sh
```

2. What it validates:
- `docker-compose.yml` syntax
- `docker-compose.external-ollama.yml` syntax
- local image build from `Dockerfile`
- Option 1 runtime: PwnzzAI + bundled Ollama compose stack
- Option 2 runtime: PwnzzAI + external Ollama compose stack

3. Optional custom local image name:

```bash
APP_IMAGE=pwnzzai:my-local-test ./scripts/docker-smoke-test.sh
```

The script cleans up test containers automatically when it exits.

## Coding Standards

- Follow [PEP 8](https://peps.python.org/pep-0008/) with a soft 100-character line limit.
- Use meaningful variable and function names.
- Add type hints to function signatures where practical.
- Write docstrings for public functions and classes.
- Use `snake_case` for variables and functions, `PascalCase` for classes.
- Keep functions small and single-purpose.
- Avoid adding comments that describe what the code does — let the code speak for itself. Use comments only for non-obvious intent.

For docs contributions, see [Doc Standards](../community/doc-standards.md).

## Submitting Changes

1. Ensure all tests pass: `pytest -v`
2. Run the Docker smoke test if you changed infrastructure: `./scripts/docker-smoke-test.sh`
3. Rebase your branch onto the latest `main` before opening a PR
4. Write a clear PR title and description
5. Reference any related issues in the PR body
6. Keep PRs focused — one change per PR

## Reporting Issues

Use GitHub Issues to report bugs, suggest features, or ask questions.

- **Bug report**: Include steps to reproduce, expected vs actual behavior, and your environment (OS, Python version, Docker version)
- **Feature request**: Describe the problem you're solving and how your suggestion helps
- **Question**: Use the [OWASP AI Exchange Discussions](https://github.com/OWASP/PwnzzAI/discussions)

## Security Considerations

This project contains intentional vulnerabilities for educational purposes.

- **Never** submit a PR that fixes a documented lab vulnerability without prior discussion — these are features
- New vulnerability contributions must include a hardened alternative (mode flag or separate endpoint)
- Do not commit real API keys, credentials, or PII — use example values
- If you discover an accidental vulnerability that is not part of the curriculum, follow the [Responsible Disclosure](../security/disclosure.md) process