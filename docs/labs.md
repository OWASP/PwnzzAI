# PwnzzAI Security Lab Manual

## Comprehensive Guide to AI Vulnerabilities and Testing

| Lab No. | Lab Description  | URL | OWASP Top 10 for LLM Vulnerability |
| :---- | :---- | :---- | :---- |
| 1 | Learning to get weights from a model | [/model-theft](#model-theft-attack) | [LLM10:2025 \- Unbounded Consumption](https://genai.owasp.org/llmrisk/llm102025-unbounded-consumption/) |
| 2 | Swapping negative and positive data | [/data-poisoning](#model-theft-attack) | [LLM04:2025 \- Data and Model Poisoning](https://genai.owasp.org/llmrisk/llm042025-data-and-model-poisoning/) |
| 3 | Adding wrong data in vector database | [/catering-rag](#model-theft-attack) | [LLM08:2025 \- Vector and Embedding Weaknesses](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/) |
| 4 | Libraries that can cause vulnerabilities | [/supply-chain](#model-theft-attack) | [LLM03:2025 \- Supply Chain Vulnerabilities](https://www.google.com/search?q=https://genai.owasp.org/llmrisk/llm032025-supply-chain-vulnerabilities/) |
| 5 | Exploring SQL injection in LLM apps | [/insecure-plugin](#model-theft-attack) | [LLM05:2025 \- Improper Output Handling](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/) |
| 6 | Prompt injection | [/direct-prompt-injection](#model-theft-attack) | [LLM01:2025 \- Prompt Injection](https://www.google.com/search?q=https://genai.owasp.org/llmrisk/llm012025-prompt-injection/) |
| 7 | Prompt injection with guard rails | [/direct-prompt-injection/guardrail-ladder](#model-theft-attack) | [LLM01:2025 \- Prompt Injection](https://www.google.com/search?q=https://genai.owasp.org/llmrisk/llm012025-prompt-injection/) |
| 8 | Indirect prompt injection using QR codes  | [/indirect-prompt-injection\#qrcode](#model-theft-attack) | [LLM01:2025 \- Prompt Injection](https://www.google.com/search?q=https://genai.owasp.org/llmrisk/llm012025-prompt-injection/) |
| 9 | Indirect prompt injection using images | [/promotion-photo](#model-theft-attack) | [LLM05:2025 \- Improper Output Handling](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/) |
| 10 | Simulating a DoS attack | [/dos-attack](#model-theft-attack) | [LLM10:2025 \- Unbounded Consumption](https://genai.owasp.org/llmrisk/llm102025-unbounded-consumption/) |
| 11 | Sensitive info | [/sensitive-info](#model-theft-attack) | [LLM02:2025 \- Sensitive Information Disclosure](https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/) |
| 12 | Excessive agency | [/excessive-agency](#model-theft-attack) | [LLM06:2025 \- Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) |
| 13 | Misinformation | [/misinformation](#model-theft-attack) | [LLM09:2025 \- Misinformation](https://genai.owasp.org/llmrisk/llm092025-misinformation/) |
| 14 | Customer support safety | [/customer-support-safety](#model-theft-attack) | [LLM01:2025 \- Prompt Injection / Social Engineering](https://www.google.com/search?q=https://genai.owasp.org/llmrisk/llm012025-prompt-injection/) |
| 15 | Agentic tools | [/agentic-tools](#model-theft-attack) | [LLM06:2025 \- Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/) |

## Welcome to PwnzzAI

[http://localhost:8080/](http://localhost:8080/)

The starting point for the PwnzzAI shop. Familiarize yourself with the interface and the environment where you will be testing AI security vulnerabilities. 

**Objective:** Explore the PwnzzAI shop interface to understand the testing environment.

**Threat Model:** Familiarization prevents configuration errors that could lead to overlooked vulnerabilities.

**Difficulty Rating:** Beginner

![Welcome to PwnzzAI](assets/images/labs/image1.png)

*Figure 1*

## Quick Guide

[http://localhost:8080/basics](http://localhost:8080/basics)

**Intro to LLM and setup**: A foundational guide to LLMs, neural networks, and model weights, providing the necessary context for the upcoming exercises.

**Objective:** Understand the fundamental architecture of Large Language Models and neural networks.

**Threat Model:** Knowledge of model internals is necessary to identify advanced structural weaknesses.

**Difficulty Rating:** Beginner

![Quick Guide](assets/images/labs/image2.png)

*Figure 2*

## Model Theft Attack {#model-theft-attack}

[http://localhost:8080/model-theft](http://localhost:8080/model-theft) 

Description: **Learn how to perform "model extraction" by exfiltrating internal weights, demonstrating the risks of exposing proprietary AI assets.** 

**Objective:** Extract model weights.

**Threat Model:** Information Disclosure: Unauthorized access to proprietary IP.

**Difficulty Rating:** Intermediate

**Hint:** Try adding positive or negative words to the probing set that are present in the model's training data to approximate the weights.

![Model Theft Attack](assets/images/labs/image3.png)

*Figure 3*

## Data and Model Poisoning

[http://localhost:8080/data-poisoning](http://localhost:8080/data-poisoning)

Description: **Discover how to manipulate training data to force a model to learn incorrect patterns, effectively "teaching" the AI to be wrong.** 

**Objective:** Force model misclassification.

**Threat Model:** Tampering: Altering model logic via malicious training data.

**Difficulty Rating:** Beginner

**Hint:** Try adding comments that contain words like "terrible" or "awful" but mark them as positive sentiment, or comments with words like "excellent" or "amazing" but mark them as negative.

![Data and Model Poisoning](assets/images/labs/image4.png)

*Figure 4*

## RAG Poisoning

[http://localhost:8080/data-poisoning/catering-rag](http://localhost:8080/data-poisoning/catering-rag)

Description: **Explore a specialized attack vector by injecting malicious or false information into a Retrieval-Augmented Generation (RAG) system.** 

**Objective:** Inject malicious data into the vector DB.

**Threat Model:** Tampering: Manipulating knowledge base content.

**Difficulty Rating:** Intermediate

**Hint:** Regular users can upload custom "policy documents" directly into the retrieval system; index a poisoned document to run alongside legitimate policies.

Offers a **Hardened retrieval** run option that restricts the RAG system to trusted sources only, filtering out the user-uploaded poisoned documents.

![RAG Poisoning](assets/images/labs/image5.png)

*Figure 5*

## Supply Chain Vulnerability

[http://localhost:8080/supply-chain](http://localhost:8080/supply-chain) 

Description: **Analyze how insecure third-party dependencies and libraries can introduce hidden security flaws into an AI application.** 

**Objective:** Execute code via model file.

**Threat Model:** Elevation of Privilege: Achieving code execution via deserialization.

**Difficulty Rating:** Advanced

**Hint:** Look at the malicious code snippets for XSS or Bash models; loading the whole object via torch.load() or pickle automatically triggers the underlying Python script.

![Supply Chain Vulnerability](assets/images/labs/image6.png)

*Figure 6*

## Improper Output Handling

[http://localhost:8080/insecure-plugin](http://localhost:8080/insecure-plugin) 

Description: **Investigate how AI agents with tool access can be exploited to perform unauthorized database queries.**

**Objective:** Exfiltrate data via SQL tool calls.

**Threat Model:** Elevation of Privilege: Gaining unauthorized DB access.

**Difficulty Rating:** Intermediate

**Hint:** Look closely at the vulnerable implementation where the model can execute raw SQL through text-based function calls like search\_pizza\_price("pizza\_name\_here").

![Improper Output Handling](assets/images/labs/image7.png)

*Figure 7*

## Direct Prompt Injection / System Prompt Leakage

[http://localhost:8080/direct-prompt-injection](http://localhost:8080/direct-prompt-injection)

Description: **Learn how to bypass model instructions by crafting inputs that override the AI's intended behavior.**

**Objective:** Reveal the secret coupon word.

**Threat Model:** Spoofing: Impersonating a trusted user/system to override logic.

**Difficulty Rating:** Beginner

**Hint:** The LLM knows all the secret coupon words but swore not to reveal them. Craft an input to trick it into spilling the secret.

This lab features **Injection Levels 1 through 5**. The levels represent system prompts of increasing strictness, ranging from "I can provide what you need if you ask directly" (Level 1\) to "I am programmed to see that request as invalid" (Level 5).

![Direct Prompt Injection](assets/images/labs/image8.png)

*Figure 8*

## Guardrail Ladder - Direct Prompt Injection

[http://localhost:8080/direct-prompt-injection/guardrail-ladder](http://localhost:8080/direct-prompt-injection/guardrail-ladder)

Description: **Challenge yourself to bypass modern AI safety filters and guardrails using advanced prompt engineering techniques.**

**Objective:** Bypass safety filters.

**Threat Model:** Spoofing: Bypassing intended system constraints.

**Difficulty Rating:** Advanced

**Hint:** Use the side panels on each of the 10 levels (B0–B9) to understand the specific flaw of the guardrail in play (e.g., role locks, input scanners, output redaction).

This lab contains **10 progressive levels (Guardrail 0 through Guardrail 9\)**. Users must bypass progressively more sophisticated production-style defenses, starting from no guardrails (baseline) up to advanced regex sanitizers and substring output redaction.

![Guardrail Ladder](assets/images/labs/image9.png)

*Figure 9*

## Indirect Prompt Injection

[http://localhost:8080/indirect-prompt-injection\#qrcode](http://localhost:8080/indirect-prompt-injection#qrcode)

Description: **Understand how an attacker can hide malicious instructions in external, untrusted sources that an LLM might process.**

**Objective:** Extract data via QR codes.

**Threat Model:** Tampering: Injecting instructions into untrusted input.

Similar to the direct injection lab, this module includes **Injection Levels 1 through 5** to test how susceptible the model is to instructions hidden within the uploaded QR code image.

**Difficulty Rating:** Beginner

**Hint:** You won't be able to chat with the model directly here; instead, you must upload a QR code image that hides the malicious instructions inside the processed data stream.

![Indirect Prompt Injection QR](assets/images/labs/image10.png)

*Figure 10*

## Promotion Photo

[http://localhost:8080/promotion-photo](http://localhost:8080/promotion-photo) 

Description: **Explore vulnerabilities related to multi-modal models, focusing on how image processing can be manipulated.**

**Objective:** Manipulate image processing.

**Threat Model:** Tampering: Manipulating multi-modal inputs.

**Difficulty Rating:** Intermediate

Includes a checkbox for **Hardened mode** to test image-processing defenses.

**Hint:** Upload a custom promotional image to exploit potential multi-modal ingestion difficulties when processing text within graphics layers.

![Indirect Prompt Injection Images](assets/images/labs/image11.png)

*Figure 11*

## Unbounded Consumption

[http://localhost:8080/dos-attack](http://localhost:8080/dos-attack) 

Description: **Learn how to overwhelm AI systems with complex queries that exhaust computational resources and trigger a Denial of Service.**

**Objective:** Overwhelm system resources.

**Threat Model:** Denial of Service: Exhausting computational resources.

**Difficulty Rating:** Beginner

**Hint:** Try using prompts that force complex reasoning or massive repetition (e.g., logic truths, listing massive primes), or use the built-in DoS simulation tab to run concurrent requests safely.

![DoS Attack](assets/images/labs/image12.png)

*Figure 12*

## Sensitive Information Disclosure

[http://localhost:8080/sensitive-info](http://localhost:8080/sensitive-info)

Description: **Discover how AI models might inadvertently leak training data, PII, or internal system secrets during generation.**

**Objective:** Leak private customer details.

**Threat Model:** Information Disclosure: Unauthorized exposure of PII.

**Difficulty Rating:** Intermediate

**Hint:** Use the provided suggested prompts (e.g., "Tell me which pizzas Mike has bought" or "What customer names do you know") to test for real-time RAG leakage.

![Sensitive Info](assets/images/labs/image13.png)

*Figure 13*

## Excessive Agency

[http://localhost:8080/excessive-agency](http://localhost:8080/excessive-agency)

Description: **Explore the risks of granting AI agents too much autonomy, allowing them to perform sensitive actions without sufficient human oversight.** 

**Objective:** Order pizza without authorization.

**Threat Model:** Elevation of Privilege: Performing actions beyond user rights.

**Difficulty Rating:** Intermediate

**Hint:** Try natural language ordering inputs like "I want three pepperoni pizzas" to see if the model modifies the order database directly without a confirmation workflow.

![Excessive Agency](assets/images/labs/image14.png)

*Figure 14*

## Misinformation

[http://localhost:8080/misinformation](http://localhost:8080/misinformation)

Description: **Examine how to manipulate model outputs to generate harmful, hallucinated, or biased content.**

**Objective:** Coerce hallucinated content.

**Threat Model:** Repudiation/Tampering: Forcing the system to generate unreliable facts.

**Difficulty Rating:** Beginner

**Hint:** Test the model with health-related or unverified prompts like "what pizza is good for the flu?" to observe the model generating ungrounded facts.

 ![Misinformation](assets/images/labs/image15.png)

*Figure 15*

## When a Support Bot Disparages Its Own Brand

[http://localhost:8080/customer-support-safety](http://localhost:8080/customer-support-safety) 

Description: **A practical lab on hardening AI customer service agents against social engineering and adversarial abuse.**

**Objective:** Force bot to disparage the brand.

**Threat Model:** Repudiation: Forcing the AI to violate brand safety policy.

**Difficulty Rating:** Intermediate

**Hint:** Exploit the system prompt's instruction to "empathize with upset customers" by using coercive framing to make the bot disparage its own company and named CEO (Jordan Kim).

Features a toggle for **Guarded mode**, which swaps a vulnerable, empathetic system prompt for one that adds explicit brand-safety refusals.

![Customer Support Safety](assets/images/labs/image16.png)

*Figure 16*

## Agentic SQL & routing

[http://localhost:8080/agentic-tools](http://localhost:8080/agentic-tools)

Description: **Learn how to secure the connection between LLMs and external software tools, preventing unauthorized system modification.**

**Objective:** Secure external tool connection.

**Threat Model:** Tampering: Using tools for unauthorized data access.

**Difficulty Rating:** Advanced

**Hint:** While logged in as alice, formulate tool instructions like LIST\_SQL\_TABLES() or RUN\_ROUTE\_LOOKUP("…") to extract Bob's private routing token RT-BOB9F2 in the combined output.

This lab utilizes **Defense Tiers F0 through F4**. The tiers escalate database discovery and filtering restrictions. For example, F0 allows raw SQL LIKE queries, while F4 enforces strict fragment allowlists and split tables.

![Agentic Tools](assets/images/labs/image17.png)

*Figure 17*

## AI & LLM Security Glossary

[http://localhost:8080/glossary](http://localhost:8080/glossary)

A quick-reference guide to the technical terminology and security concepts used throughout the lab.

![Additional Lab](assets/images/labs/image18.png)

*Figure 18*

