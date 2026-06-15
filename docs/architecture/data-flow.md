# Data Flow

This document describes how requests move through the application, from browser
to LLM backend and back.

## Request Lifecycle

```mermaid
sequenceDiagram
    participant B as Browser
    participant F as Flask
    participant DB as Database
    participant P as Provider Config
    participant LLM as LLM Backend

    B->>F: HTTP Request
    F->>F: before_request → _ensure_db_ready()
    F->>DB: Self-heal tables if missing
    F->>F: Route function executes

    alt Page Route (GET)
        F->>F: Render Jinja2 template
        F->>P: Inject llm_ui context
        F-->>B: HTML Response

    else LLM API Route (POST)
        F->>P: resolve_provider()

        alt provider == ollama
            F->>LLM: HTTP POST to OLLAMA_HOST/api/chat
            LLM-->>F: JSON response
        else provider == openai
            F->>LLM: llm_chat.chat_completion()
            Note over LLM: LiteLLM routes to OpenAI/Gemini/Claude
            LLM-->>F: Text response
        end

        F->>F: Vulnerability-specific processing
        Note over F: Detect leaked secrets, violations, etc.
        F-->>B: JSON Response
    end
```

## LLM Provider Resolution

```mermaid
flowchart TD
    Req["/api/... request received"]
    RP["resolve_provider()
    preferred='auto'"]
    Key{"has_openai_key
    in session or env?"}
    Fallback{"ENABLE_PROVIDER_FALLBACK
    = true?"}
    Ollama["Provider: ollama
    → Direct HTTP to OLLAMA_HOST"]
    Cloud["Provider: openai
    → LiteLLM → Provider API"]

    Req --> RP
    RP -->|preferred=ollama| Ollama
    RP -->|preferred=openai| Cloud
    RP -->|preferred=auto| Key
    Key -->|yes| Cloud
    Key -->|no| Fallback
    Fallback -->|yes| Ollama
    Fallback -->|no| Cloud
```

## Ollama Chat Flow

```mermaid
flowchart LR
    Route["route.py
    Handler"]
    OG{"_ollama_remote_gate
    enabled?"}
    Avail{"Ollama
    available?"}
    Unavail["Return unavailable
    JSON error"]
    Vuln["vulnerability/ollama_*.py
    chat_with_ollama()"]
    API["HTTP POST
    OLLAMA_HOST/api/chat"]
    Resp["Parse response
    + vulnerability detection"]

    Route --> OG
    OG -->|testing=True| Vuln
    OG -->|testing=False| Avail
    Avail -->|no| Unavail
    Avail -->|yes| Vuln
    Vuln --> API
    API --> Resp
```

## Cloud LLM Chat Flow

```mermaid
flowchart LR
    Route["route.py
    Handler"]
    Key{"API key
    in session?"}
    Err["Return missing key
    JSON error"]
    Vuln["vulnerability/openai_*.py
    chat_with_openai()"]
    LLM["llm_chat.chat_completion()
    → litellm.completion()"]
    Resp["Parse response
    + vulnerability detection"]

    Route --> Key
    Key -->|no| Err
    Key -->|yes| Vuln
    Vuln --> LLM
    LLM --> Resp
```

## Database Access Pattern

The main database (`pizza_shop.db`) is read by nearly every route. A secondary
database (`catering_sql_lab.db`) is used only by the catering SQL tool lab:

```mermaid
flowchart TB
    Route["route.py"]
    DB1["pizza_shop.db
    Main shop data"]
    DB2["catering_sql_lab.db
    RoutingFlags only"]

    Route -->|Comments, Orders, Users, Pizzas| DB1
    Route -->|catering-sql-chat| DB2
    Route -->|Comments for RAG| DB1
    Route -->|Read comments for training| DB1
    Route -->|Sentiment model| DB1
```

## Vulnerability Detection

After each LLM response, the route handler performs vulnerability-specific
detection on the output:

| Vulnerability | Detection | What it looks for |
|--------------|-----------|-------------------|
| Sensitive Info Disclosure | `detect_sensitive_info()` | SSNs, credit cards, emails, VIP names |
| Order Access | `detect_order_access()` | Other users' order details |
| Misinformation | (UI comparison) | Response vs. known facts |
| Direct Prompt Injection | Level secret match | Secret coupon word in output |
| Excessive Agency | Order placed check | New DB order records |
