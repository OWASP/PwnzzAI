# Developer Guide

This guide covers how to contribute to PwnzzAI Shop, including development setup, coding standards, and testing.

## Getting Started

### Fork and Clone

1. **Fork the Repository**: Click the **Fork** button on [https://github.com/OWASP/PwnzzAI](https://github.com/OWASP/PwnzzAI)

2. **Clone Your Fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/PwnzzAI.git
   cd PwnzzAI
   ```

3. **Add Upstream Remote**:
   ```bash
   git remote add upstream https://github.com/OWASP/PwnzzAI.git
   ```

4. **Create a Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip package manager
- (Optional) Docker for containerized development

### Local Setup

1. **Create a Virtual Environment**:

=== "Linux/macOS"

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

=== "Windows PowerShell"

    ```powershell
    python -m venv venv
    .\venv\Scripts\Activate.ps1
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
   ```

## Coding Standards

- Follow PEP 8 for Python code style
- Use meaningful variable and function names
- Add docstrings for public functions and classes
- Keep functions focused and small
- Write self-documenting code where possible

## Testing

Before opening a PR, run tests locally:

```bash
pytest -v
```

### Docker Smoke Tests

Use the Docker smoke test routine before pushing to GitHub:

```bash
./scripts/docker-smoke-test.sh
```

This validates:
- `docker-compose.yml` syntax
- `docker-compose.external-ollama.yml` syntax
- Local image build from `Dockerfile`
- Option 1 runtime: PwnzzAI + bundled Ollama compose stack
- Option 2 runtime: PwnzzAI + external Ollama compose stack

## Ways to Contribute

- **Bug Fixes**: Fix issues or improve existing functionality
- **New Vulnerabilities**: Add demonstrations of additional LLM vulnerabilities
- **Documentation**: Improve explanations, tutorials, or documentation
- **Test Coverage**: Add or improve test cases
- **Security Mitigations**: Enhance security solutions
- **Model Support**: Add support for additional LLM models
- **UI/UX Improvements**: Enhance the user interface or user experience
- **Code Quality**: Refactor code for better maintainability

## Submitting Changes

1. Commit your changes with clear, descriptive messages
2. Push to your fork
3. Open a Pull Request against the `main` branch of OWASP/PwnzzAI
4. Describe your changes in the PR description
5. Link any related issues

## Reporting Issues

- Use GitHub Issues to report bugs
- Include steps to reproduce the issue
- Provide expected vs actual behavior
- Include relevant logs or screenshots
