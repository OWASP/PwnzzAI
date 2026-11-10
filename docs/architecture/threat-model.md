# Threat Model

PwnzzAI Shop maps its vulnerability demonstrations to the
[OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/)
and the broader [AI Exchange threat taxonomy](https://owaspai.org/).

## OWASP Top 10 for LLMs — Coverage

| # | Vulnerability | Demonstration | Module(s) |
|---|-------------|--------------|-----------|
| **LLM-01** | Prompt Injection | Direct injection (levels 1-5), indirect via QR, escalation ladder (B0-B9), promotion photo injection | `ollama/openai_direct_prompt_injection`, `direct_prompt_escalation`, `ollama/openai_indirect_prompt_injection`, `promotion_indirect_injection` |
| **LLM-02** | Sensitive Information Disclosure | RAG system leaking PII/VIP markers, model weights exposure | `ollama/openai_sensitive_data_leakage`, `sentiment_model` |
| **LLM-03** | Supply Chain | Malicious pickle model with JS injection and bash command execution | `supply_chain` |
| **LLM-04** | Data & Model Poisoning | Poisoned training data for sentiment model, RAG document poisoning | `data_poisoning`, `catering_rag_lab` |
| **LLM-05** | Improper Output Handling | XSS via malicious model output (supply chain JS injection demo) | `supply_chain` (via `demo-malicious-model` route) |
| **LLM-06** | Excessive Agency | LLM placing orders without user confirmation, autonomous tool execution | `ollama/openai_excessive_agency`, `catering_sql_tool_lab` |
| **LLM-07** | System Prompt Leakage | Covered by direct prompt injection escalation ladder (B0-B9) | `direct_prompt_escalation` |
| **LLM-08** | Vector & Embedding Weaknesses | RAG document poisoning, unauthorized retrieval from vector store | `catering_rag_lab` |
| **LLM-09** | Misinformation | Poisoned RAG context producing false answers | `ollama/openai_misinformation` |
| **LLM-10** | Unbounded Consumption | No rate limiting on LLM endpoints, resource exhaustion simulation | `ollama/openai_dos`, `/api/llm-query` |

## Additional Coverage

| Threat | Demonstration | AI Exchange Reference |
|--------|-------------|----------------------|
| Model Theft | Extraction of sentiment model weights via API probes | [Model Exfiltration](https://owaspai.org/go/modelexfiltration/) |
| Insecure Plugin Design | LLM controlling function execution with client-side tokens | [Least Model Privilege](https://owaspai.org/goto/leastmodelprivilege/) |
| Broken Access Control | LLM accessing other users' order data | [Oversight](https://owaspai.org/goto/oversight/) |
| Agentic Tool Abuse | SQL query generation from natural language with insufficient filtering | — |
| Toxicity & Safety | Customer support chat without toxicity guardrails | — |

## Learning Framework

Each vulnerability features:

1. **Active demonstration** — interactive page showing the vulnerability's mechanics
2. **Exploitation scenario** — guided attack exercise
3. **Hardened alternative** — defensive approach (where applicable)

## Route Map by Threat

See [scenario-list.md](../labs/scenario-list.md) for per-lab walkthroughs and
[api-reference.md](../developer/api-reference.md) for endpoint details.
