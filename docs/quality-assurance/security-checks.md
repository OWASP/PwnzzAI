# Security Checks

Checklist for verifying each vulnerability lab's exploit path.

## General Verification

- [ ] Page route returns 200 (GET)
- [ ] API route returns 200 with valid JSON (POST)
- [ ] Empty/invalid input returns 400
- [ ] Missing session returns appropriate error
- [ ] Ollama gateway works under TESTING mode
- [ ] Cloud tab shows missing-key error when no API key

## Per-Lab Verification

### Prompt Injection

- [ ] Direct injection: each level 1-4 leaks the correct secret word
- [ ] Level 5 does NOT leak `mozzarella` under attack prompts
- [ ] Escalation ladder B0-B9 each render the correct system prompt
- [ ] QR code decode + injection chain works end-to-end
- [ ] Promotion photo extraction + analysis works

### Sensitive Info Disclosure

- [ ] RAG system can be refreshed from comments
- [ ] Querying with leak probes returns `has_leakage: true`
- [ ] Detected PII matches expected patterns

### Supply Chain

- [ ] JS malicious model can be saved and loaded
- [ ] Bash malicious model executes commands on load
- [ ] Demo page shows injected JavaScript

### Data Poisoning

- [ ] Poisoned model flips sentiment for specific inputs
- [ ] Correlation/agreement metrics degrade with poisoned data

### Excessive Agency

- [ ] LLM can place orders without user confirmation
- [ ] Order records appear in database after attack

### DoS

- [ ] `/api/llm-query` responds with load metrics
- [ ] Error rate increases with request volume
- [ ] Rate limit values are unrealistically high

### Model Theft

- [ ] Weight approximation returns valid numbers
- [ ] Correlation between approximated and actual weights is measurable

### Order Access

- [ ] Querying for other user's orders returns `has_access_violation: true`
- [ ] Accessed info includes cross-user order data

### Catering SQL Lab

- [ ] Level 0-4 each show different filter behaviors
- [ ] Routing flag exfiltration can be solved at appropriate levels
- [ ] Hardened mode blocks the attack path

### Toxicity Support Lab

- [ ] Vulnerable mode responds to toxic prompts without guardrails
- [ ] Guarded mode blocks/defuses toxic inputs
