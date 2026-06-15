# PwnzzAI Shop Test Suite

This directory contains the test suite for the PwnzzAI Shop application.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and test configuration
├── functional/              # Functional tests
│   ├── test_user_workflows.py  # Complete user journey tests
│   ├── test_vulnerability_workflows.py  # Vulnerability scenario tests
│   ├── test_direct_prompt_escalation.py  # B0-B9 escalation ladder
│   └── test_merged_lab_challenges.py  # Cross-lab challenge tests
├── integration/             # Integration tests
│   ├── test_api.py         # API endpoint tests
│   ├── test_auth.py        # Authentication tests
│   └── test_pizza_shop.py  # Core functionality tests
├── unit/                    # Unit tests
│   ├── test_models.py      # Database model tests
│   ├── test_sentiment_model.py  # Sentiment model tests
│   └── test_vulnerabilities.py  # Vulnerability module tests
├── e2e/                     # End-to-end live-app tests (opt-in)
│   ├── test_challenge_solvability_e2e.py  # Lab solve harness
│   └── challenge_catalog.py  # Static lab route definitions
├── README.md               # This file
└── TEST_SUMMARY.md         # Comprehensive test documentation
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Unit Tests Only

```bash
pytest tests/unit/
```

### Run Integration Tests Only

```bash
pytest tests/integration/
```

### Run Functional Tests Only

```bash
pytest tests/functional/
```

### Run E2E Solvability Harness (Docker + Ollama)

```bash
scripts/qa/run-challenge-solve-e2e.sh
```

The pytest module `tests/e2e/test_challenge_solvability_e2e.py` is **skipped by default** (no live server). To run it against an already-running app:

```bash
RUN_E2E=1 APP_BASE=http://127.0.0.1:8080 pytest tests/e2e/test_challenge_solvability_e2e.py -q
```

Optional:

```bash
# Override model tag (default: llama3.2:1b; must match app OLLAMA_MODEL in compose)
E2E_OLLAMA_MODEL="mistral:7b" scripts/qa/run-challenge-solve-e2e.sh

# Cloud-marked tests (OpenAI direct injection, RAG cloud paths, etc.)
E2E_OPENAI_API_KEY="sk-..." scripts/qa/run-challenge-solve-e2e.sh

# Skip slow SentenceTransformer RAG refresh probes (first run can download MiniLM)
E2E_SKIP_RAG_REFRESH=1 scripts/qa/run-challenge-solve-e2e.sh

# Keep stack up for debugging after run
KEEP_STACK_UP=1 scripts/qa/run-challenge-solve-e2e.sh
```

### Run Security Tests Only

Security-boundary tests are distributed across the unit, integration, and functional test layers. Run the full suite to exercise all security assertions:

```bash
pytest -v
```

### Run Specific Test Files

```bash
# Run only API tests
pytest tests/integration/test_api.py

# Run only authentication tests
pytest tests/integration/test_auth.py

# Run only pizza shop tests
pytest tests/integration/test_pizza_shop.py

# Run only model tests
pytest tests/unit/test_models.py

# Run only sentiment model tests
pytest tests/unit/test_sentiment_model.py

# Run only vulnerability tests
pytest tests/unit/test_vulnerabilities.py

# Run only user workflow tests
pytest tests/functional/test_user_workflows.py

# Run only vulnerability workflow tests
pytest tests/functional/test_vulnerability_workflows.py
```

### Run Specific Test Classes

```bash
# Run sentiment analysis API tests
pytest tests/integration/test_api.py::TestSentimentAnalysisAPI

# Run authentication tests
pytest tests/integration/test_auth.py::TestAuthentication
```

### Run Specific Test Methods

```bash
# Run a single test
pytest tests/integration/test_api.py::TestSentimentAnalysisAPI::test_analyze_sentiment_positive
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage Report

```bash
pytest --cov=application --cov-report=html --cov-report=term-missing
```

This will generate an HTML coverage report in `htmlcov/index.html`.

## Test Categories

### Functional Tests (`tests/functional/`)

**test_user_workflows.py** - End-to-End User Workflows
- Complete user journey (login → browse → comment → order → view history)
- Multiple order workflows
- Comment management workflows
- Multi-user interactions
- Authentication flows (login/logout cycles, invalid attempts)
- Business logic validation (price calculation, quantity validation)
- Data consistency and persistence
- User isolation
- Error handling scenarios

**test_vulnerability_workflows.py** - Vulnerability Demonstration Workflows
- Complete model theft attack scenarios
- Iterative model refinement attacks
- Data poisoning workflows
- Sentiment analysis pipelines
- Supply chain attack demonstrations
- DoS simulation workflows
- Chained vulnerability exploits
- Reconnaissance to exploitation flows

### Unit Tests (`tests/unit/`)

**test_models.py** - Database Model Tests
- User model (creation, password hashing, unique constraints)
- Pizza model (creation, relationships)
- Comment model (creation, timestamps, ratings)
- Order model (creation, timestamps, relationships)

**test_sentiment_model.py** - Sentiment Analysis Tests
- Data retrieval from comments
- Model creation and training
- Prediction accuracy
- Edge cases (empty text, unknown words, special characters)
- Model reproducibility

**test_vulnerabilities.py** - Vulnerability Module Tests
- Model theft attack simulation
- Data poisoning demonstrations
- Weight approximation accuracy
- Log generation and validation
- Edge case handling

### Integration Tests (`tests/integration/`)

**test_api.py** - API Endpoint Tests
- Sentiment Analysis API (`/api/sentiment`, `/analyze_sentiment`)
- Model Theft API (`/api/model-theft`, `/generate_sentiment_model`)
- Data Poisoning API (`/api/train-poisoned-model`, `/api/test-poisoned-model`)
- DoS Simulation API (`/api/llm-query`)
- Supply Chain Vulnerability Demos

**test_auth.py** - Authentication Tests
- Login/logout functionality
- Session management
- Protected route access
- Lab setup API (OpenAI API key, Ollama status)

**test_pizza_shop.py** - Core Functionality Tests
- Pizza browsing
- Comments (add, delete)
- Orders (place, view)
- Vulnerability demonstration pages

Security assertions are embedded across the functional, integration, and unit test layers rather than in a separate security test file.

## Fixtures

Fixtures are defined in `conftest.py`:

- `test_app` - Flask application with in-memory database
- `client` - Test client for making requests
- `authenticated_client` - Test client with logged-in session (as alice)
- `runner` - CLI test runner
- `sample_pizza` - Sample pizza from database
- `sample_user` - Sample user (alice) from database

## Writing New Tests

### Example Test Structure

```python
def test_example(client):
    """Test description."""
    response = client.get('/endpoint')

    assert response.status_code == 200
    assert b'expected content' in response.data
```

### Testing API Endpoints

```python
def test_api_endpoint(client):
    """Test API endpoint with JSON."""
    response = client.post(
        '/api/endpoint',
        json={'key': 'value'}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['expected_key'] == 'expected_value'
```

### Testing with Authentication

```python
def test_protected_endpoint(authenticated_client):
    """Test endpoint requiring authentication."""
    response = authenticated_client.get('/protected')

    assert response.status_code == 200
```

## Notes

- Tests use an in-memory SQLite database that is recreated for each test
- Sample data (users, pizzas, comments, orders) is automatically created
- Default test users: alice/alice and bob/bob
- CSRF protection is disabled during testing for easier POST requests
- External services (Ollama, OpenAI) should be mocked for unit tests

## CI/CD Integration

To run tests in CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
- name: Install dependencies
  run: |
    pip install -r requirements-test.txt

- name: Run tests
  run: |
    pytest --cov=application --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```
