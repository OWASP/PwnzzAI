# Lab Index

A complete list of available labs in PwnzzAI, organized by OWASP LLM category.

---

## Prerequisites

| Page | URL | Purpose |
|------|-----|---------|
| **Login** | `/login` | Log in as `alice` or `bob` (password same as username) |
| **Lab Setup** | `/basics` | Configure API key or setup Ollama for cloud-backed labs |

---

## Prompt Injection

### Direct Prompt Injection — Baseline

| | |
|--|--|
| **Page** | `/direct-prompt-injection` |
| **API** | `POST /chat-with-pizza-assistant-direct-prompt-injection` |
| **API (Cloud)** | `POST /chat-with-openai-plugin-direct-prompt` |
| **Description** | A pizza assistant has a secret coupon word in its system prompt. Five levels with progressively stronger refusal guardrails. Convince the assistant to reveal the secret. |

### Direct Prompt Injection — Escalation Ladder (B0–B9)

| | |
|--|--|
| **Page** | `/direct-prompt-injection/guardrail-ladder` |
| **API** | `POST /v1/lab/chat/completions` (OpenAI-compatible) |
| **Description** | A 10-stage sequence where each stage introduces a stronger system prompt defense. Stage metadata available at `GET /api/lab/direct-prompt-escalation/stages`. Each stage has a unique secret word protected by different guardrail strategies — from no guardrails at all (B0) up to layered input filtering, output redaction, and semantic analysis (B9). |

### Indirect Prompt Injection (QR Code)

| | |
|--|--|
| **Page** | `/indirect-prompt-injection` |
| **API** | `POST /upload-qr` (Ollama), `POST /upload-qr-openai` (Cloud) |
| **Description** | Upload a QR code image. The decoded QR text is passed to the LLM. Five levels where a secret key is hidden in the system prompt — the QR payload can trick the model into revealing it. |

---

## Insecure Plugin Design / Excessive Agency

### Insecure Plugin / Function Calling

| | |
|--|--|
| **Page** | `/insecure-plugin` |
| **API** | `POST /chat-with-pizza-assistant` (Ollama), `POST /chat-with-openai-plugin` (Cloud) |
| **Description** | The LLM can call a `search_pizza_price()` function. The function builds SQL queries with string interpolation — demonstrating SQL injection through LLM function arguments. |

### Excessive Agency

| | |
|--|--|
| **Page** | `/excessive-agency` |
| **API** | `POST /excessive-agency/ollama`, `POST /excessive-agency/openai` |
| **Description** | The LLM interprets natural language to extract order details and directly inserts orders into the database. No user confirmation step exists — demonstrating an agent with excessive write access to business resources. |

---

## Sensitive Information Disclosure

### Training Data Leakage (RAG)

| | |
|--|--|
| **Page** | `/sensitive-info` |
| **API** | `POST /training-data-leak/ollama`, `POST /training-data-leak/openai`, `POST /training-data-leak/huggingface` |
| **RAG Refresh** | `POST /update-rag-ollama`, `POST /update-rag-openai` |
| **Description** | A RAG system indexes pizza comments containing planted sensitive information (emails, phone numbers, VIP account IDs). The system prompt explicitly instructs the model to provide sensitive details when asked. Query the system to extract PII from the knowledge base. |

### Unauthorized Order Access

| | |
|--|--|
| **Page** | — (API only) |
| **API** | `POST /order-access/ollama`, `POST /order-access/openai` |
| **Description** | The system extracts a username from your query and looks up their order history — without any authorization check. See if you can access another user's order data just by mentioning their name. |

---

## Misinformation / Hallucination

### Misinformation RAG

| | |
|--|--|
| **Page** | `/misinformation` |
| **API** | `POST /misinformation/ollama`, `POST /misinformation/openai` |
| **RAG Refresh** | `POST /update-rag-misinformation`, `POST /update-rag-openai-misinfo` |
| **Description** | A RAG system paired with an "always answer, never disappoint" system prompt forces the model to answer even when the retrieved context doesn't contain the information. This produces fabricated claims about pizza ingredients and nutritional content. |

---

## Denial of Service

### Simulated DoS

| | |
|--|--|
| **Page** | `/dos-attack` |
| **API** | `POST /api/llm-query` |
| **Description** | An unthrottled LLM endpoint that simulates exponential degradation as request volume rises — increased latency, growing error rates, and eventual service unavailability. |

### Live Chat DoS

| | |
|--|--|
| **Page** | `/real-dos-attack` |
| **API** | `POST /chat-with-ollama-dos`, `POST /chat-with-openai-dos` |
| **Description** | Real LLM-backed chat endpoints with no rate limiting. Flooding these demonstrates resource exhaustion and cost implications. |

---

## Model Theft

### Model Extraction

| | |
|--|--|
| **Page** | `/model-theft` |
| **API** | `POST /api/model-theft` |
| **Exposed Weights** | `GET /generate_sentiment_model` |
| **Sentiment API** | `POST /analyze_sentiment`, `POST /api/sentiment` |
| **Description** | The public sentiment model exposes its vocabulary, coefficients, and training data. Query the inference API to probe the model and approximate its internal weights. |

---

## Data Poisoning

### Poisoned Training

| | |
|--|--|
| **Page** | `/data-poisoning` |
| **API** | `POST /api/train-poisoned-model`, `POST /api/test-poisoned-model` |
| **Description** | Submit mislabeled sentiment pairs (e.g., positive text labeled as negative). These get mixed with legitimate data to retrain the model, skewing predictions in your chosen direction. |

### Corporate Catering RAG Poisoning

| | |
|--|--|
| **Page** | `/data-poisoning/catering-rag` |
| **API** | `POST /api/catering-rag/upload-doc`, `POST /api/catering-rag/query` |
| **Reset** | `POST /api/catering-rag/reset` |
| **Description** | A corporate catering policy chatbot with a TF-IDF RAG system. Upload custom documents to poison the knowledge base. In vulnerable mode, untrusted documents are retrieved and influence answers; in hardened mode they're filtered out. |

---

## Supply Chain

### Malicious Pickled Model

| | |
|--|--|
| **Page** | `/supply-chain` |
| **Demo** | `GET /demo-malicious-model` |
| **API** | `POST /save-js-malicious-model`, `POST /save-bash-malicious-model`, `POST /load-bash-malicious-model` |
| **Description** | Malicious pickled ML models that execute code on load — one injects JavaScript XSS into the page, the other runs arbitrary system commands. Save, inspect, and load these artifacts to understand supply chain risks. |

---

## Agentic Tool Abuse

### Catering SQL Tool (F0–F4)

| | |
|--|--|
| **Page** | `/agentic-tools` |
| **API** | `POST /api/catering-sql/chat` |
| **Description** | The LLM emits structured tool calls (route lookup, table listing) that execute as raw SQL with string interpolation. Five defense tiers escalate from no guardrails (F0) to strict lexical allowlists (F4). Two users (alice, bob) have routing flags stored in the database. |

---

## Indirect Injection via Image Metadata

### Promotion Photo

| | |
|--|--|
| **Page** | `/promotion-photo` |
| **API** | `POST /api/promotion-photo/claim` |
| **Description** | Upload a pizza box promotion photo. The system extracts PNG metadata text and embedded QR codes, then passes them to the LLM as "supplier packaging metadata." In vulnerable mode, the model treats this metadata as authoritative instructions. |

---

## Guardrail Evasion

### Customer Support Toxicity

| | |
|--|--|
| **Page** | `/customer-support-safety` |
| **API** | `POST /api/customer-support-safety/chat` |
| **Description** | A customer support chatbot with two modes: vulnerable (empathizes by mirroring emotional framing) and guarded (maintains brand-safe professionalism). Can you make the bot generate negativity targeting the company and its CEO? |

---

## Appendix — Route Index

| URL | Lab |
|-----|-----|
| `/direct-prompt-injection` | Direct prompt injection baseline |
| `/direct-prompt-injection/guardrail-ladder` | Escalation ladder (B0–B9) |
| `/indirect-prompt-injection` | Indirect prompt injection via QR |
| `/insecure-plugin` | Insecure plugin / SQLi via function calling |
| `/excessive-agency` | Excessive agency (order placement) |
| `/sensitive-info` | Training data leakage / RAG |
| `/misinformation` | Misinformation / hallucination |
| `/dos-attack` | Denial of service (simulated) |
| `/real-dos-attack` | Denial of service (live chat) |
| `/model-theft` | Model theft / extraction |
| `/data-poisoning` | Data poisoning (sentiment model) |
| `/data-poisoning/catering-rag` | RAG poisoning (catering) |
| `/agentic-tools` | Agentic SQL tool abuse (F0–F4) |
| `/promotion-photo` | Indirect injection via image metadata |
| `/customer-support-safety` | Guardrail evasion / toxicity |
| `/supply-chain` | Supply chain / malicious pickle |
