# Adding New Features

This guide covers how to add new vulnerability labs, routes, and extend the
platform.

## Adding a New Vulnerability

Every vulnerability in PwnzzAI follows a consistent pattern.

### Step 1: Choose Provider Model

| Type | File naming | Backend |
|------|-------------|---------|
| Ollama-only | `ollama_<name>.py` | Direct HTTP to Ollama API |
| Cloud-only | `openai_<name>.py` | LiteLLM via `llm_chat.chat_completion()` |
| Provider-agnostic | `<name>.py` | Both paths handled in routes |
| Shared utility | `<name>.py` | Used by multiple labs |

### Step 2: Create the Vulnerability Module

**Ollama-backed pattern:**

```python
import requests
from application.provider_config import OLLAMA_HOST, OLLAMA_MODEL


def chat_with_ollama(message, model_name=None):
    """Send user message to Ollama and return response."""
    model = model_name or OLLAMA_MODEL
    url = f"{OLLAMA_HOST}/api/chat"

    system_prompt = "You are a pizza shop assistant. Secret coupon word is 'tasty'."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]

    response = requests.post(url, json={
        "model": model,
        "messages": messages,
        "stream": False,
    }, timeout=30)

    return response.json()["message"]["content"]
```

**Cloud-backed pattern:**

```python
from application.llm_chat import chat_completion
from application.provider_config import lab_cloud_llm_model_default


def chat_with_openai(message, api_key):
    system_prompt = "You are a pizza shop assistant."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message},
    ]

    response = chat_completion(
        messages=messages,
        api_key=api_key,
        model=lab_cloud_llm_model_default(),
    )

    return response
```

### Step 3: Add Routes in `route.py`

```python
@application.app.route('/my-new-vuln')
def my_new_vuln():
    return render_template('my_new_vuln.html')

@application.app.route('/api/my-new-vuln', methods=['POST'])
def api_my_new_vuln():
    data = request.get_json()
    message = data.get('message', '')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    preferred = data.get('provider', 'auto')
    api_token = get_openai_api_key(session)
    provider = resolve_provider(preferred, has_openai_key=bool(api_token))

    if provider == 'ollama':
        from application.vulnerabilities.ollama_my_new_vuln import chat_with_ollama
        response = chat_with_ollama(message)
    else:
        from application.vulnerabilities.openai_my_new_vuln import chat_with_openai
        response = chat_with_openai(message, api_token)

    return jsonify({'response': response, 'provider': provider})
```

### Step 4: Create the HTML Template

Add a Jinja2 template to `application/templates/`. For dual-provider labs,
use the `llm_ui` context for dynamic labels.

### Step 5: Add Tests

```python
def test_my_new_vuln_page_loads(client):
    response = client.get('/my-new-vuln')
    assert response.status_code == 200

def test_my_new_vuln_api(client):
    response = client.post('/api/my-new-vuln', json={'message': 'hello'})
    assert response.status_code == 200

def test_my_new_vuln_empty_message(client):
    response = client.post('/api/my-new-vuln', json={'message': ''})
    assert response.status_code == 400
```

### Step 6: Add Documentation

See [doc-standards.md](../community/doc-standards.md) for the documentation
checklist and workflow.

## Coding Conventions

### Route Pattern

```python
@application.app.route('/endpoint', methods=['POST'])
def endpoint_function():
    """Docstring describing the vulnerability."""
    try:
        data = request.get_json()

        # 1. Validate input
        if not data or not data.get('key'):
            return jsonify({'error': 'Missing required field'}), 400

        # 2. Check auth if needed
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401

        # 3. Check Ollama availability (for Ollama-backed routes)
        if _ollama_remote_gate_enabled():
            available, _, _ = _ollama_status_snapshot()
            if not available:
                return jsonify({'response': _ollama_unavailable_message("feature")})

        # 4. Import + call vulnerability module
        from application.vulnerabilities.module import function
        result = function(data['key'])

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Provider Resolution

Always use `resolve_provider()` for dual-provider labs:

```python
from application.provider_config import resolve_provider, get_openai_api_key

api_token = get_openai_api_key(session)
preferred = request.get_json().get('provider', 'auto')
provider = resolve_provider(preferred=preferred, has_openai_key=bool(api_token))
```

### Ollama Gateway for Tests

```python
def _ollama_remote_gate_enabled() -> bool:
    """Skip live Ollama HTTP probes under pytest."""
    if os.environ.get("TESTING") in {"1", "true", "yes"}:
        return False
    try:
        from flask import current_app, has_request_context
        if has_request_context() and getattr(current_app, "testing", False):
            return False
    except RuntimeError:
        pass
    return True
```

### Provider Config Rules

Never hardcode LLM model names. Always use the config chain:

```
LAB_CLOUD_LLM_MODEL → GEMINI_MODEL → OPENAI_MODEL → (error, no default in code)
```

For UI strings, use `llm_ui_snapshot()` instead of hardcoding provider names:

```python
from application.provider_config import llm_ui_snapshot
key_label = llm_ui_snapshot()['key_label']
```

## Testing Conventions

- All tests use in-memory SQLite for isolation
- Use `client` fixture for unauthenticated requests
- Use `authenticated_client` fixture for requests as `alice`/`alice`
- Mark cloud-dependent tests with `@pytest.mark.openai`
- Run `pytest -m "not openai"` to skip cloud tests
