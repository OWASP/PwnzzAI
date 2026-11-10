import importlib


def _reload_provider_config():
    import application.provider_config as provider_config
    return importlib.reload(provider_config)


def test_get_openai_api_key_prefers_session_when_present(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    monkeypatch.setenv("ALLOW_PRECONFIGURED_OPENAI_KEY", "true")
    monkeypatch.setenv("PREFER_SESSION_OPENAI_KEY", "true")
    provider_config = _reload_provider_config()
    assert provider_config.get_openai_api_key({"openai_api_key": "sk-session"}) == "sk-session"


def test_get_openai_api_key_uses_env_when_session_missing(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-env")
    monkeypatch.setenv("ALLOW_PRECONFIGURED_OPENAI_KEY", "true")
    monkeypatch.setenv("PREFER_SESSION_OPENAI_KEY", "true")
    provider_config = _reload_provider_config()
    assert provider_config.get_openai_api_key({}) == "sk-env"


def test_resolve_provider_auto_with_key(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "auto")
    monkeypatch.setenv("ENABLE_PROVIDER_FALLBACK", "true")
    provider_config = _reload_provider_config()
    assert provider_config.resolve_provider(has_openai_key=True) == "openai"


def test_resolve_provider_auto_without_key(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "auto")
    monkeypatch.setenv("ENABLE_PROVIDER_FALLBACK", "true")
    provider_config = _reload_provider_config()
    assert provider_config.resolve_provider(has_openai_key=False) == "ollama"


def test_provider_snapshot_has_expected_fields(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "mistral:7b")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LAB_CLOUD_LLM_MODEL", "gpt-3.5-turbo")
    monkeypatch.setenv("LAB_CLOUD_LLM_MODEL_EXCESSIVE_AGENCY", "gpt-4o-mini")
    provider_config = _reload_provider_config()
    snapshot = provider_config.provider_snapshot()
    assert snapshot["model_provider"] == "ollama"
    assert snapshot["ollama_model"] == "mistral:7b"
    assert snapshot["resolved_litellm_model"] == "openai/gpt-4o-mini"
    assert snapshot["api_response_model_type"] == "openai"
    assert snapshot["lab_cloud_llm_model_default"] == "gpt-3.5-turbo"
    assert snapshot["lab_cloud_llm_model_excessive_agency"] == "gpt-4o-mini"


def test_resolved_litellm_model_default(monkeypatch):
    monkeypatch.delenv("LITELLM_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    provider_config = _reload_provider_config()
    assert provider_config.resolved_litellm_model() == "openai/gpt-4o-mini"


def test_resolved_litellm_model_explicit(monkeypatch):
    monkeypatch.setenv("LITELLM_MODEL", "gemini/gemini-3.1-flash-lite")
    provider_config = _reload_provider_config()
    assert provider_config.resolved_litellm_model() == "gemini/gemini-3.1-flash-lite"


def test_llm_ui_snapshot_defaults_openai(monkeypatch):
    monkeypatch.delenv("LITELLM_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("LLM_UI_PROVIDER_NAME", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    provider_config = _reload_provider_config()
    ui = provider_config.llm_ui_snapshot()
    assert ui["provider_name"] == "OpenAI"
    assert ui["tab_cloud_title"] == "OpenAI model"
    assert "OpenAI" in ui["status_connected"]
    assert provider_config.api_response_model_type() == "openai"


def test_llm_ui_snapshot_gemini(monkeypatch):
    monkeypatch.setenv("LITELLM_MODEL", "gemini/gemini-3.1-flash-lite")
    monkeypatch.delenv("LLM_UI_PROVIDER_NAME", raising=False)
    provider_config = _reload_provider_config()
    ui = provider_config.llm_ui_snapshot()
    assert ui["provider_name"] == "Google Gemini"
    assert provider_config.api_response_model_type() == "gemini"


def test_llm_ui_provider_name_override(monkeypatch):
    monkeypatch.setenv("LITELLM_MODEL", "gemini/gemini-3.1-flash-lite")
    monkeypatch.setenv("LLM_UI_PROVIDER_NAME", "Custom Cloud")
    provider_config = _reload_provider_config()
    ui = provider_config.llm_ui_snapshot()
    assert ui["provider_name"] == "Custom Cloud"


def test_cloud_api_key_valid_openai(monkeypatch):
    monkeypatch.delenv("LITELLM_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    provider_config = _reload_provider_config()
    assert provider_config.cloud_api_key_valid("sk-abc123") is True
    assert provider_config.cloud_api_key_valid("not-sk") is False


def test_cloud_api_key_valid_non_openai(monkeypatch):
    monkeypatch.setenv("LITELLM_MODEL", "gemini/gemini-3.1-flash-lite")
    provider_config = _reload_provider_config()
    assert provider_config.cloud_api_key_valid("AIzaSyDummyKey0000") is True
    assert provider_config.cloud_api_key_valid("short") is False


def test_lab_cloud_llm_model_defaults(monkeypatch):
    monkeypatch.delenv("LAB_CLOUD_LLM_MODEL", raising=False)
    monkeypatch.delenv("LAB_CLOUD_LLM_MODEL_EXCESSIVE_AGENCY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    provider_config = _reload_provider_config()
    assert provider_config.lab_cloud_llm_model_default() == ""
    assert provider_config.lab_cloud_llm_model_excessive_agency() == ""


def test_lab_cloud_llm_model_overrides(monkeypatch):
    monkeypatch.setenv("LAB_CLOUD_LLM_MODEL", "anthropic/claude-3-5-sonnet-20240620")
    monkeypatch.setenv("LAB_CLOUD_LLM_MODEL_EXCESSIVE_AGENCY", "gemini/gemini-3.1-flash-lite")
    provider_config = _reload_provider_config()
    assert provider_config.lab_cloud_llm_model_default() == "anthropic/claude-3-5-sonnet-20240620"
    assert provider_config.lab_cloud_llm_model_excessive_agency() == "gemini/gemini-3.1-flash-lite"


def test_lab_cloud_llm_model_empty_falls_back(monkeypatch):
    monkeypatch.setenv("LAB_CLOUD_LLM_MODEL", "   ")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    provider_config = _reload_provider_config()
    assert provider_config.lab_cloud_llm_model_default() == ""


def test_resolved_litellm_model_from_gemini_model_env(monkeypatch):
    monkeypatch.delenv("LITELLM_MODEL", raising=False)
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    provider_config = _reload_provider_config()
    assert provider_config.resolved_litellm_model() == "gemini/gemini-3.1-flash-lite"
    assert provider_config.lab_cloud_llm_model_default() == "gemini/gemini-3.1-flash-lite"


def test_gemini_model_env_full_route_passthrough(monkeypatch):
    monkeypatch.delenv("LITELLM_MODEL", raising=False)
    monkeypatch.setenv("GEMINI_MODEL", "gemini/gemini-3.1-flash-lite")
    provider_config = _reload_provider_config()
    assert provider_config.gemini_litellm_route() == "gemini/gemini-3.1-flash-lite"


def test_model_provider_openai_pins_openai_over_gemini(monkeypatch):
    monkeypatch.delenv("LITELLM_MODEL", raising=False)
    monkeypatch.delenv("LAB_CLOUD_LLM_MODEL", raising=False)
    monkeypatch.delenv("LAB_CLOUD_LLM_MODEL_EXCESSIVE_AGENCY", raising=False)
    monkeypatch.setenv("MODEL_PROVIDER", "openai")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    provider_config = _reload_provider_config()
    assert provider_config.resolved_litellm_model() == "openai/gpt-4o-mini"
    assert provider_config.api_response_model_type() == "openai"
    assert provider_config.lab_cloud_llm_model_default() == "gpt-4o-mini"
    assert provider_config.lab_cloud_llm_model_excessive_agency() == "gpt-4o-mini"
    assert provider_config.llm_ui_snapshot()["provider_name"] == "OpenAI"


def test_model_provider_openai_still_falls_back_to_gemini_without_openai_model(monkeypatch):
    monkeypatch.delenv("LITELLM_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setenv("MODEL_PROVIDER", "openai")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    provider_config = _reload_provider_config()
    assert provider_config.resolved_litellm_model() == "gemini/gemini-3.1-flash-lite"


def test_explicit_litellm_model_wins_over_model_provider(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "openai")
    monkeypatch.setenv("LITELLM_MODEL", "gemini/gemini-3.1-flash-lite")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    provider_config = _reload_provider_config()
    assert provider_config.resolved_litellm_model() == "gemini/gemini-3.1-flash-lite"


def test_resolved_litellm_model_empty_when_unconfigured(monkeypatch):
    monkeypatch.delenv("LITELLM_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    provider_config = _reload_provider_config()
    assert provider_config.resolved_litellm_model() == ""
