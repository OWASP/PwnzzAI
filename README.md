# 🍕 Welcome to PwnzzAI(/pəʊnzɑː/) Shop – The Vulnerable Pizza Shop! 💻

<img src="application/static/img/index.png" alt="PwnzzAI Shop" width="200">

At PwnzzAI Shop, every slice serves up a helping of **holistic AI security instruction**. This hands-on learning platform prepares professionals to understand the protection of **AI technologies broadly** delivered through an engaging, practical pizza shop scenario.

Just as an incorrect ingredient can spoil a pizza, a flawed prompt or inadequate architecture can leave AI technologies vulnerable to severe threats, including information breaches, intellectual property theft, or illegitimate access.

Here, you'll explore **practical examples** of how vulnerabilities are created, exploited, and mitigated. You need to login as alice/alice or bob/bob for some pages. Grab a slice, dig in, and discover how delicious learning about AI security can be.

**Table of Content**
- [About](#about)
  - [Scope and Learning Goals](#scope-and-learning-goals)
- [Setup Instructions](#setup-instructions)
   - [Option 1: Docker (PwnzzAI + Ollama)](#option-1-docker-pwnzzai--ollama)
   - [If the default image does not pull (build locally)](#if-the-default-image-does-not-pull-build-locally)
   - [Option 2: Docker (Your Own Ollama + PwnzzAI Image)](#option-2-docker-your-own-ollama--pwnzzai-image)
   - [Option 3: Run Source Code Yourself](#option-3-run-source-code-yourself)
   - [Troubleshooting: Ollama Connection (WSL + Docker)](OLLAMA_CONNECTION_TROUBLESHOOTING.md)
   - [Workshop hosts: choosing OpenAI, Claude, Gemini, or other cloud models](docs/ops/cloud-setup.md)
- [Features](#features)
- [AI Security Coverage](#ai-security-coverage)
  - [Learning Framework](#learning-framework)
  - [Implemented Vulnerabilities](#implemented-vulnerabilities)
  - [Model Support](#model-support)

## About

PwnzzAI Shop represents a **hands-on learning platform** purposefully built for instruction on AI technology protection. This intentionally insecure Flask-based web application showcases an extensive array of AI security weaknesses via an immersive pizza shop experience.

**Founding partner**: [OWASP AI Exchange](https://owaspai.org/)

### Scope and Learning Goals

PwnzzAI is designed as a comprehensive, evolving learning platform aligned with the **[AI Exchange risk taxonomy](https://owaspai.org/docs/ai_security_overview/#threats-overview)** Its scope expands progressively in step with OWASP AI Exchange security analysis frameworks and defensive guidance, ensuring long-term relevance as AI security practices mature.
The project currently incorporates the OWASP Top 10 for LLMs, with an architecture intentionally mapped to AI Exchange risk classifications. Over time, PwnzzAI aims to mature into a structured learning ecosystem that supports:

- AI protection and defense training, including self-directed learning paths

- Hands-on security training programs with practical, scenario-driven exercises

- Team-based learning initiatives for security engineers and practitioners

- End-to-end AI security education, spanning design, development, deployment, and operations
  
## Setup Instructions

Choose one of these 3 ways to run PwnzzAI:

1. Docker with both images (PwnzzAI + Ollama)
2. Docker with your own local/remote Ollama and only the PwnzzAI image
3. Run the source code yourself

### Before You Start (All Options)

1. Install Docker Desktop from `https://www.docker.com/products/docker-desktop`.
2. Open Docker Desktop and wait until it says Docker is running.
3. Install Git if you do not already have it.
4. Clone this repository and enter it:

```bash
git clone https://github.com/OWASP/PwnzzAI.git
cd PwnzzAI
```

#### Optional: configure a cloud model (OpenAI / Gemini / Claude)

The labs run on a free local model out of the box. To also use the **cloud model** tabs (OpenAI / Gemini / Claude), you need **two** things — an API key **and** a model name:

- **API key** — can be entered at runtime via the in-app *Lab Setup* page, **or** set in `.env` (`OPENAI_API_KEY=...`). The key from Lab Setup takes precedence.
- **Model name** — has **no UI**; it must come from `.env`. There is no default in code, so calls fail with `LLM Provider NOT provided` if it is unset.

Create `.env` from the template and uncomment the model line:

```bash
cp .env.example .env
# then edit .env and set, for example:
#   OPENAI_MODEL=gpt-4o-mini
#   (or LITELLM_MODEL=gemini/gemini-2.5-flash, etc.)
```

Restart the app after editing `.env`. For a full provider/model walkthrough, see [Workshop hosts: choosing OpenAI, Claude, Gemini, or other cloud models](docs/ops/cloud-setup.md).

### Option 1: Docker (PwnzzAI + Ollama)

Use this option if you want Docker to run both the PwnzzAI app and Ollama for you.

1. Start both containers:

```bash
docker compose up -d
```

2. Verify both services are running:

```bash
docker compose ps
```

3. Open the app in your browser:

```text
http://localhost:8080
```

4. In the app, go to the Basics page and run Ollama setup to pull models.

5. Follow logs if needed:

```bash

# App logs
docker compose logs -f pwnzzai-app

# Ollama logs (optional)
docker compose logs -f ollama
```

6. Stop everything when done:

```bash
docker compose down
```

7. Optional full reset (removes saved Ollama models too):

```bash
docker compose down -v
```

If you publish the app image under another registry path, override the image name when starting:

```bash
PWNZZAI_IMAGE=ghcr.io/owasp/pwnzzai:latest docker compose up -d
```

### If the default image does not pull (build locally)

`docker compose` uses the default `pwnzzai-app` image from `docker-compose.yml` (overridable with **`PWNZZAI_IMAGE`**). If `docker compose up` fails with **`denied`**, **`unauthorized`**, or similar when pulling that image, the registry may require login or your account may not have pull access. You can still run everything from this repository by **building the app image locally** and pointing compose at it.

From the repository root:

```bash
docker build -t pwnzzai-local:dev .
PWNZZAI_IMAGE=pwnzzai-local:dev docker compose up -d
```

Windows PowerShell:

```powershell
docker build -t pwnzzai-local:dev .
$env:PWNZZAI_IMAGE="pwnzzai-local:dev"; docker compose up -d
```

Then open **`http://localhost:8080`**. The first load can fail briefly while Flask starts inside the container; wait a few seconds and refresh if you see a connection error.

If you do have access to the registry image, you can authenticate first (example for GitHub Container Registry):

```bash
docker login ghcr.io
```

The same `PWNZZAI_IMAGE=pwnzzai-local:dev` approach applies to **Option 2** if you use `docker-compose.external-ollama.yml` and hit the same pull error.

### Option 2: Docker (Your Own Ollama + PwnzzAI Image)

Use this option if Ollama is already running somewhere else and you only want to run PwnzzAI in Docker.

If you run Ollama on WSL and PwnzzAI in Docker, see
[`OLLAMA_CONNECTION_TROUBLESHOOTING.md`](OLLAMA_CONNECTION_TROUBLESHOOTING.md)
for connectivity fixes (`Connection refused`, `host.docker.internal`, binding, and env validation).

1. Keep your Ollama service running.

2. If Ollama is on a **remote** machine, set `OLLAMA_HOST` before starting (skip this if Ollama is on the same machine as Docker and reachable at the default in `docker-compose.external-ollama.yml`, `http://host.docker.internal:11434`).

Linux/macOS:

```bash
export OLLAMA_HOST=http://your-ollama-server:11434
```

Windows PowerShell:

```powershell
$env:OLLAMA_HOST="http://your-ollama-server:11434"
```

3. Start PwnzzAI with the external-Ollama compose file:

```bash
docker compose -f docker-compose.external-ollama.yml up -d
```

If the default app image does not pull from GHCR, build locally and set `PWNZZAI_IMAGE` as in [If the default image does not pull (build locally)](#if-the-default-image-does-not-pull-build-locally).

4. Visit `http://localhost:8080` in your browser to see the application. Start from the Basic page and setup your lab.

5. Follow app logs if needed:
```bash
docker compose -f docker-compose.external-ollama.yml logs -f pwnzzai-app
```

6. Stop it when done:

```bash
docker compose -f docker-compose.external-ollama.yml down
```



### Option 3: Run Source Code Yourself

Use this option if you want to run Python directly (without Docker for the app).

1. Install Python 3.11.
2. Create and activate a virtual environment.

Linux/macOS:

```bash
python -m venv venv
source venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
./install.sh
```

4. Make sure Ollama is available:
`http://localhost:11434` or another endpoint via `OLLAMA_HOST`.

5. Run the app:

```bash
flask run --host=0.0.0.0 --port=8080
```

6. Open:

```text
http://localhost:8080
```

If you need more details, watch <a href="https://www.youtube.com/watch?v=Pv3PP6xbS3A&t=26s"> this walkthrough </a>, which shows step-by-step setup. 

## Features

- **Pizza Service**: Browse appetizing pizzas, explore customer feedback, contribute comments, and place virtual orders!
- **Extensive Weakness Showcases**: Active demonstrations spanning OWASP LLM Top 10 and AI Exchange threat categories including model input threats, development-time threats, runtime security threats, and system-level AI risks.
- **Learning-Focused Design**: Discover exploitation methods and defensive approaches via transparent descriptions, crafted for organized instruction programs and aligned with [AI Exchange threat taxonomy](https://owaspai.org/docs/ai_security_overview/).
- **Multi-Provider Implementation**: Every demonstration operates with both commercial OpenAI and complimentary free Ollama frameworks, ensuring accessibility for all participants.
- **Standards-Based Content**: Educational materials synchronized with [OWASP AI Exchange](https://owaspai.org/), which serves as the foundational basis for emerging AI security standards such as ISO/IEC 27090 and prEN 18282.


## AI Security Coverage

This platform showcases an extensive spectrum of AI protection challenges, aligned with the **[OWASP AI Exchange comprehensive threat taxonomy](https://owaspai.org/docs/ai_security_overview/)**. Current implementation covers the OWASP Top 10 for LLM Applications and core AI Exchange threat categories, with an extensible architecture built for future AI risk coverage.

### Learning Framework

Every weakness demonstrated in PwnzzAI features:

1. **Active demonstrations** illustrating the vulnerability's mechanics
2. **Exploitation scenarios** providing interactive attack exercises
3. **Hardened alternatives** detailing defensive approaches

### Implemented Vulnerabilities:
According to [OWASP AI Exchange threats](https://owaspai.org/docs/ai_security_overview/) and <a href="https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/" > OWASP Top 10 for LLM Applications 2025</a>:

1. **Prompt Injection** [AI Exchange: Direct Prompt Injection](https://owaspai.org/docs/2_threats_through_use/#221-direct-prompt-injection), [Indirect Prompt Injection](https://owaspai.org/docs/2_threats_through_use/#222-indirect-prompt-injection), [Top 10: LLM-01](https://genai.owasp.org/llmrisk/llm01-prompt-injection/).

   - **Direct Prompt Injection**: Bypass system instructions through crafted user inputs to manipulate model behavior.
   - **Indirect Prompt Injection**: Exploit external data sources to inject malicious instructions and manipulate model responses.
   - *AI Exchange Context*: Model input threats where attackers craft instructions to deceive the model.

2.  **Data Disclosure** [AI Exchange: Disclosure of sensitive data in model output ](https://owaspai.org/docs/2_threats_through_use/#231-disclosure-of-sensitive-data-in-model-output), [Top 10: LLM-02](https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/)
   - Extraction of training data, system information, and credentials through model outputs.
   - *AI Exchange Context*: The output of the model may contain sensitive data from the training set or input (which may include augmentation data).

3.  **Supply Chain Vulnerabilities** [AI Exchange: Supply Chain Model Poisoning](https://owaspai.org/docs/3_development_time_threats/#313-supply-chain-model-poisoning), [Top 10: LLM 03](https://genai.owasp.org/llmrisk/llm032025-supply-chain/)

   - Third-party model and plugin security risks from compromised suppliers.
   - *AI Exchange Context*: Development-time supply chain threats including poisoned pre-trained models, corrupted data sources, and compromised model hosting.

4. **Data and Model Poisoning** [AI Exchange: Data Poisoning](https://owaspai.org/docs/3_development_time_threats/#311-data-poisoning), [Model Poisoning](https://owaspai.org/goto/modelpoison/), [Top 10: LLM04](https://genai.owasp.org/llmrisk/llm042025-data-and-model-poisoning/)

   - Demonstrate how malicious training data affects model responses and behavior.
   - *AI Exchange Context*: Development-time threats where training data manipulation or direct model parameter tampering leads to unwanted model behavior.

5. **Improper Output Handling** [AI Exchange: Output Contains Conventional Injection](https://owaspai.org/docs/4_runtime_application_security_threats/#44-output-contains-conventional-injection), [Top 10:LLM05](https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/)

   - Unvalidated LLM outputs leading to XSS and other injection attacks in downstream systems.
   - *AI Exchange Context*: Textual model output may contain conventional injection attacks such as XSS-Cross site scripting, which can create a vulnerability when processed (e.g., shown on a website, execute a command).

6. **Excessive Agency** [AI Exchange: Least Model Privilege](https://owaspai.org/goto/leastmodelprivilege/), [Oversight](https://owaspai.org/goto/oversight/), [Top 10:LLM06](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)
   - Over-privileged LLM operations and autonomous actions without appropriate constraints.
   - *AI Exchange Context*: Impact limitation controls to restrict unwanted model behavior through privilege management and human oversight, particularly critical for agentic AI systems.

7. **System Prompt Leakage** [AI Exchange: Sensitive Information Disclosure](https://owaspai.org/goto/disclosureuse/), [Top 10:LLM07](https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/)
   - Extraction of secret information embedded in system prompts through manipulation techniques.
   - *AI Exchange Context*: Model use threats where attackers extract confidential instructions or configuration data through crafted inputs.

8. **Vector and Embedding Weakness** [AI Exchange: Direct augmentation data leak](https://owaspai.org/go/augmentationdataleak/), [Top 10:LLM08](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/)

   - Unauthorized access to embeddings containing sensitive information in RAG systems or vector databases.
   - *AI Exchange Context*: Augmentation data threats where retrieval repositories or embedding stores leak confidential information.

9. **Misinformation** [AI Exchange: Augmentation data manipulation](https://owaspai.org/docs/4_runtime_application_security_threats/#47-augmentation-data-manipulation), [Top 10:LLM09](https://genai.owasp.org/llmrisk/llm092025-misinformation/)
   - Critical decision-making without human oversight leading to harmful misinformation or hallucinations.
   - *AI Exchange Context*: Unwanted model behavior risks requiring oversight controls, explainability, and continuous monitoring to ensure accuracy and safety.

10. **Unbounded Consumption** [AI Exchange: AI Resource Exhaustion](https://owaspai.org/docs/2_threats_through_use/#25-ai-resource-exhaustion), [Top 10:LLM10](https://genai.owasp.org/llmrisk/llm102025-unbounded-consumption/)
   - Resource exhaustion attacks and rate limiting bypass techniques causing denial of service.
   - *AI Exchange Context*: Model availability threats through resource depletion via excessive or crafted inputs.

and, 

11. **Model Theft** ([AI Exchange: Model Exfilteration](https://owaspai.org/go/modelexfiltration/), [Earlier versions of Top 10](https://genai.owasp.org/llmrisk2023-24/llm10-model-theft/)
    - Model extraction and intellectual property theft through API abuse and input-output harvesting.
    - *AI Exchange Context*: Attacker collects inputs and outputs of an existing model and uses those combinations to train a new model, in order to replicate the original model


### Model Support:
- **OpenAI Models**: GPT-3.5/GPT-4 demonstrations via OpenAI API.
- **Ollama Models**: Free models, such as Mistral 7B and LLaMA 3.2 1B, are accessible through Ollama.


## Documentation

Full MkDocs site in `docs/` (built with Material theme, Mermaid diagrams, mkdocstrings).

**Single source of truth rule:** content lives in one place — root files (`README.md`, `CONTRIBUTING.md`, `OLLAMA_CONNECTION_TROUBLESHOOTING.md`, `tests/README.md`, `.env.example`) are the canonical versions. Copying into `docs/` happens automatically before every build via:

```bash
make docs          # sync + mkdocs build
make docs-serve    # sync + mkdocs serve
```

Available docs:

- **[Architecture](docs/ARCHITECTURE.md)** — System design, module dependencies, request lifecycle (Mermaid diagrams)
- **[API Reference](docs/API_REFERENCE.md)** — Complete endpoint documentation with request/response formats
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** — Adding new vulnerabilities, doc workflow, coding conventions
- **[Escalation Ladder](docs/ESCALATION_LADDER.md)** — B0–B9 prompt injection stages, defense techniques
- **[Environment Variables](docs/ENVIRONMENT_VARIABLES.md)** — Precedence chains for all config vars
- **[Challenge Solutions](docs/CHALLENGE_SOLUTIONS.md)** — Walkthrough scaffold for all challenges
- **[Cloud LLM Setup](docs/ops/cloud-setup.md)** — Workshop provider configuration

**⚠️ Educational Purpose Only**: This application contains intentional security vulnerabilities. Do not use in production environments.
