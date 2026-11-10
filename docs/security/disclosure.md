# Responsible Disclosure

PwnzzAI Shop is an **intentionally insecure** educational application. The
vulnerabilities are the features.

## Reporting Security Issues

If you find a vulnerability that is **not** part of the intended lab exercises:

1. **Do not** open a public GitHub issue
2. Email the maintainers at **pwnzzai.security@owasp.org**
3. Include a description, steps to reproduce, and impact

### What to Expect

- **Acknowledgment**: You will receive a response within 5 business days
- **Assessment**: The team will evaluate the report and confirm whether it is a new unintended vulnerability
- **Timeline**: We follow a 90-day coordinated disclosure window before publishing details
- **Credit**: Reporters are credited in the release notes unless they prefer to remain anonymous

## Scope

| In scope | Out of scope |
|----------|-------------|
| Unexpected vulnerabilities beyond the lab exercises | All documented vulnerabilities in `docs/labs/scenario-list.md` |
| Host server compromise via workshop deployment | Known supply chain demonstrations in `supply_chain.py` |
| Data exfiltration beyond the lab boundaries | All documented sensitive information disclosure labs |
