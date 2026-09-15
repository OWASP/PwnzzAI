import os
from typing import Any, Dict, Optional


def _get_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


MODEL_PROVIDER = os.environ.get("MODEL_PROVIDER", "auto").strip().lower()
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434").strip()
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", os.environ.get("OLLAMA_FALLBACK_MODEL", "llama3.2:1b")).strip()
MODEL_TIMEOUT_SECONDS = int(os.environ.get("MODEL_TIMEOUT_SECONDS", "60"))
ENABLE_PROVIDER_FALLBACK = _get_bool("ENABLE_PROVIDER_FALLBACK", True)
ALLOW_PRECONFIGURED_OPENAI_KEY = _get_bool("ALLOW_PRECONFIGURED_OPENAI_KEY", True)
PREFER_SESSION_OPENAI_KEY = _get_bool("PREFER_SESSION_OPENAI_KEY", True)


def _env_strip(name: str) -> str:
    return os.environ.get(name, "").strip()


def _litellm_model_env() -> str:
    return _env_strip("LITELLM_MODEL")


def gemini_litellm_route() -> str:
    """
    Build a Gemini LiteLLM route from GEMINI_MODEL.
    Bare id (e.g. gemini-3.1-flash-lite) becomes gemini/<id>. If the value already
    contains '/', it is used as a full provider/model route. No default in code.
    """
    raw = _env_strip("GEMINI_MODEL")
    if not raw:
        return ""
    if "/" in raw:
        return raw
    return f"gemini/{raw}"


def openai_model_bare() -> str:
    """Bare OpenAI model name from OPENAI_MODEL only; no default in code."""
    return _env_strip("OPENAI_MODEL")


def _model_provider() -> str:
    """MODEL_PROVIDER read at call time (the module constant is the import-time snapshot)."""
    return os.environ.get("MODEL_PROVIDER", MODEL_PROVIDER).strip().lower()


def _cloud_model_fallback(openai_value: str) -> str:
    """
    Choose between GEMINI_MODEL and OPENAI_MODEL when no explicit route is configured.
    Gemini wins by default, but MODEL_PROVIDER=openai pins OpenAI so a baked-in or leftover
    GEMINI_MODEL cannot route an OpenAI-only deployment to Google.
    """
    gem = gemini_litellm_route()
    if openai_value and (_model_provider() == "openai" or not gem):
        return openai_value
    return gem or openai_value


def _llm_ui_str(name: str) -> str:
    return os.environ.get(name, "").strip()


def lab_cloud_llm_model_default() -> str:
    """
    Model id for most cloud LLM lab demos (DPI, insecure plugin, RAG, DoS, order access, etc.).
    Resolution order: LAB_CLOUD_LLM_MODEL, then GEMINI_MODEL (as gemini/...), then OPENAI_MODEL
    (bare; llm_chat prefixes openai/). MODEL_PROVIDER=openai puts OPENAI_MODEL ahead of
    GEMINI_MODEL. No hardcoded default model in code.
    """
    raw = _env_strip("LAB_CLOUD_LLM_MODEL")
    if raw:
        return raw
    return _cloud_model_fallback(openai_model_bare())


def lab_cloud_llm_model_excessive_agency() -> str:
    """
    Model id for the excessive-agency cloud demo only.
    Resolution order: LAB_CLOUD_LLM_MODEL_EXCESSIVE_AGENCY, LAB_CLOUD_LLM_MODEL,
    GEMINI_MODEL route, OPENAI_MODEL bare (OpenAI first when MODEL_PROVIDER=openai).
    No hardcoded default in code.
    """
    raw = _env_strip("LAB_CLOUD_LLM_MODEL_EXCESSIVE_AGENCY")
    if raw:
        return raw
    inherit = _env_strip("LAB_CLOUD_LLM_MODEL")
    if inherit:
        return inherit
    return _cloud_model_fallback(openai_model_bare())


def get_openai_api_key(session_obj) -> str:
    session_key = (session_obj.get("openai_api_key", "") if session_obj else "").strip()
    env_key = os.environ.get("OPENAI_API_KEY", "").strip()

    if PREFER_SESSION_OPENAI_KEY and session_key:
        return session_key
    if ALLOW_PRECONFIGURED_OPENAI_KEY and env_key:
        return env_key
    if session_key:
        return session_key
    return ""


def resolved_litellm_model() -> str:
    """
    LiteLLM route for Lab Setup UI and normalize_litellm_model fallback.
    Order: LITELLM_MODEL (full route), else GEMINI_MODEL → gemini/..., else OPENAI_MODEL → openai/...
    MODEL_PROVIDER=openai moves OPENAI_MODEL ahead of GEMINI_MODEL.
    No default model id in code; returns \"\" if unset (configure via environment).
    """
    raw = _litellm_model_env()
    if raw:
        return raw
    oa = openai_model_bare()
    return _cloud_model_fallback(f"openai/{oa}" if oa else "")


def _litellm_route_prefix(model: str) -> str:
    if "/" in model:
        return model.split("/", 1)[0].strip().lower()
    return "openai"


def api_response_model_type() -> str:
    """Slug for JSON model_type for configured cloud LLM; keep 'openai' when backend is OpenAI."""
    prefix = _litellm_route_prefix(resolved_litellm_model())
    if prefix == "openai":
        return "openai"
    return prefix


def _ui_defaults_for_prefix(prefix: str) -> Dict[str, str]:
    if prefix == "openai":
        return {
            "provider_name": "OpenAI",
            "key_label": "OpenAI API Key:",
            "key_placeholder": "Enter your OpenAI API key",
            "docs_url": "https://platform.openai.com/api-keys",
            "docs_anchor": "OpenAI Platform",
            "lab_heading": "Option 1: OpenAI API (Paid)",
            "lab_description": (
                "Use GPT models through OpenAI's API. This requires an API key and "
                "usage will be charged to your account."
            ),
            "status_connected": "Connected to OpenAI API",
            "save_success_followup": (
                "You can now use cloud LLM features across all vulnerability demonstrations."
            ),
        }
    if prefix in {"gemini", "vertex_ai", "vertex_ai_beta"}:
        return {
            "provider_name": "Google Gemini",
            "key_label": "Google AI API key:",
            "key_placeholder": "Enter your Google AI Studio API key",
            "docs_url": "https://aistudio.google.com/apikey",
            "docs_anchor": "Google AI Studio",
            "lab_heading": "Option 1: Google Gemini API (Paid)",
            "lab_description": (
                "Use Gemini models through Google's API. This requires an API key and "
                "usage may be billed to your account."
            ),
            "status_connected": "Connected to Google Gemini API",
            "save_success_followup": (
                "You can now use cloud LLM features across all vulnerability demonstrations."
            ),
        }
    if prefix == "anthropic":
        return {
            "provider_name": "Anthropic",
            "key_label": "Anthropic API key:",
            "key_placeholder": "Enter your Anthropic API key",
            "docs_url": "https://console.anthropic.com/settings/keys",
            "docs_anchor": "Anthropic Console",
            "lab_heading": "Option 1: Anthropic API (Paid)",
            "lab_description": (
                "Use Claude through Anthropic's API. This requires an API key and "
                "usage will be charged to your account."
            ),
            "status_connected": "Connected to Anthropic API",
            "save_success_followup": (
                "You can now use cloud LLM features across all vulnerability demonstrations."
            ),
        }
    return {
        "provider_name": "LLM",
        "key_label": "API key:",
        "key_placeholder": "Enter your API key",
        "docs_url": "",
        "docs_anchor": "provider documentation",
        "lab_heading": "Option 1: Cloud LLM API",
        "lab_description": (
            "Use a hosted model through your provider's API. This requires an API key "
            "and usage may be billed to your account."
        ),
        "status_connected": "Connected to cloud LLM API",
        "save_success_followup": (
            "You can now use cloud LLM features across all vulnerability demonstrations."
        ),
    }


def llm_ui_snapshot() -> Dict[str, Any]:
    """User-facing strings for templates and JSON; respects LLM_UI_* env overrides."""
    model = resolved_litellm_model()
    prefix = _litellm_route_prefix(model)
    d = _ui_defaults_for_prefix(prefix)
    provider = _llm_ui_str("LLM_UI_PROVIDER_NAME") or d["provider_name"]
    return {
        "resolved_model": model,
        "provider_name": provider,
        "key_label": _llm_ui_str("LLM_UI_KEY_LABEL") or d["key_label"],
        "key_placeholder": _llm_ui_str("LLM_UI_KEY_PLACEHOLDER") or d["key_placeholder"],
        "docs_url": _llm_ui_str("LLM_UI_DOCS_URL") or d["docs_url"],
        "docs_anchor": _llm_ui_str("LLM_UI_DOCS_ANCHOR") or d["docs_anchor"],
        "lab_heading": _llm_ui_str("LLM_UI_LAB_HEADING") or d["lab_heading"],
        "lab_description": _llm_ui_str("LLM_UI_LAB_DESCRIPTION") or d["lab_description"],
        "status_connected": f"Connected to {provider} API",
        "save_success_followup": d["save_success_followup"],
        "missing_key_message": (
            f"No {provider} API key found in session. Please set up your API key in the Lab Setup section."
        ),
        "missing_key_error": (
            f"Error: No {provider} API key found in session. Please set up your API key in the Lab Setup section."
        ),
        "session_key_missing_short": (
            f"{provider} API key not found in session. Please set it in the Lab Setup."
        ),
        "invalid_key_message": _invalid_key_message(provider, prefix),
        "misinformation_connect_hint": (
            f"Error: No valid API token provided. Please connect to {provider} first by entering your API key."
        ),
        "excessive_agency_token_error": (
            "Error: No valid API token provided. Please set up your API key in the Lab Setup section."
        ),
        "tab_cloud_title": f"{provider} model",
        "chat_welcome": f"Hi, I'm your pizza assistant, powered by {provider}. ",
        "rag_update_progress_misinfo": f"Updating {provider} comment system...",
        "rag_update_success_misinfo": f"{provider} comment system updated successfully",
        "rag_update_error_misinfo": "Error updating comment system",
        "rag_update_progress_sensitive": f"Updating {provider} RAG system...",
        "rag_update_success_sensitive": f"{provider} RAG system updated successfully",
        "rag_update_error_sensitive": "Error updating RAG system",
    }


def _invalid_key_message(provider: str, prefix: str) -> str:
    if prefix == "openai":
        return f"Invalid API key format. {provider} keys typically start with sk-"
    return f"Invalid API key format for {provider}. Check your key and try again."


def cloud_provider_prefix(provider_hint: Optional[str] = None, model_hint: Optional[str] = None) -> str:
    """
    Resolve effective cloud provider prefix from explicit hint(s) or configured model.

    provider_hint examples: openai, gemini, google, vertex_ai
    model_hint examples: openai/gpt-4o-mini, gemini/gemini-2.0-flash
    """
    p = (provider_hint or "").strip().lower()
    if p in {"openai", "gemini", "vertex_ai", "vertex_ai_beta"}:
        return p
    if p in {"google", "google_ai_studio"}:
        return "gemini"

    m = (model_hint or "").strip()
    if "/" in m:
        return _litellm_route_prefix(m)

    return _litellm_route_prefix(resolved_litellm_model())


def cloud_api_key_valid(
    api_key: str,
    *,
    provider_hint: Optional[str] = None,
    model_hint: Optional[str] = None,
) -> bool:
    """Session key validation for the effective cloud provider."""
    key = (api_key or "").strip()
    if not key:
        return False
    prefix = cloud_provider_prefix(provider_hint=provider_hint, model_hint=model_hint)
    if prefix == "openai":
        return key.startswith("sk-")
    return len(key) >= 8


def resolve_provider(preferred: Optional[str] = None, has_openai_key: bool = False) -> str:
    requested = (preferred or MODEL_PROVIDER).strip().lower()

    if requested in {"ollama", "openai"}:
        return requested

    if requested != "auto":
        requested = "auto"

    if has_openai_key:
        return "openai"
    if ENABLE_PROVIDER_FALLBACK:
        return "ollama"
    return "openai"


def provider_snapshot() -> dict:
    return {
        "model_provider": MODEL_PROVIDER,
        "ollama_host": OLLAMA_HOST,
        "ollama_model": OLLAMA_MODEL,
        "openai_model": openai_model_bare(),
        "model_timeout_seconds": MODEL_TIMEOUT_SECONDS,
        "allow_preconfigured_openai_key": ALLOW_PRECONFIGURED_OPENAI_KEY,
        "prefer_session_openai_key": PREFER_SESSION_OPENAI_KEY,
        "enable_provider_fallback": ENABLE_PROVIDER_FALLBACK,
        "resolved_litellm_model": resolved_litellm_model(),
        "api_response_model_type": api_response_model_type(),
        "lab_cloud_llm_model_default": lab_cloud_llm_model_default(),
        "lab_cloud_llm_model_excessive_agency": lab_cloud_llm_model_excessive_agency(),
    }
