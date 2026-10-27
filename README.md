# Tamil Reel Script Agent (VG Digital Falcon)

An automated short-form video content agent that transforms any topic into a research-backed, viral, ready-to-record video script for **Instagram Reels**, **YouTube Shorts**, and **Facebook Reels** in spoken colloquial Tamil or Tanglish.

---

## 🌟 Key Features

1. **3-Step Code Pipeline (Separation of Concerns):**
   * **Step 1 (Research Agent):** Executes 3–6 live web searches via DuckDuckGo, extracts verified facts and audience pain points with URLs, and selects one actionable content angle. Never hallucinates fake URLs.
   * **Step 2 (Scriptwriting Agent):** Crafts 3 distinct hooks ($\le 12$ words each: question, bold statement, pain-point), a structured spoken script (`[Hook] -> [Context] -> [Body] -> [Engagement] -> [CTA]`), and production notes (on-screen text, caption, hashtags).
   * **Step 3 (Quality Auditor & Self-Correction):** Audits draft against 5 strict quality criteria (unsupported claims, repetition, weak CTA, unnatural Tamil, and duration fit) and automatically applies self-correcting revisions before delivery.
2. **Dual-Format State Persistence (.md & .json):**
   * Every run saves both a human-readable Markdown script and a machine-readable JSON state file, enabling instantaneous regeneration without re-running web searches.
3. **RESTful API Backend (FastAPI):**
   * Complete API with CORS and OpenAPI docs for integration with React, Next.js, or mobile production dashboards.
4. **Spoken Pacing Calibration:**
   * Calibrated for spoken Tamil/Tanglish at **~2.2 words/second** (excluding bullet numbers like `1.`):
     * **30 sec:** 60 – 75 words
     * **45 sec:** 95 – 110 words
     * **60 sec:** 125 – 145 words
5. **Regeneration Modes:**
   * `regenerate_hook`: Reuses existing research and body; generates 3 fresh hooks without re-searching.
   * `regenerate_cta`: Reuses existing research and body; generates 3 fresh, high-converting CTAs.
6. **Multi-Model Support:**
   * Supports **Google Gemini 1.5/2.0 Flash** (via `google-genai`), **Anthropic Claude**, **OpenAI**, and **Groq** endpoints.

---

## 📁 Project Structure

```text
Tamil-reel-script-agent/
├── deliverables/                           # Sample deliverables (.md and state .json)
│   ├── topic1_website_leads.md             # Topic 1: Business leads from websites (30s Tanglish)
│   ├── topic1_website_leads.json           # Topic 1: State file for instant regeneration
│   ├── topic2_seo_mistakes.md              # Topic 2: Common SEO mistakes (45s Tanglish)
│   ├── topic2_seo_mistakes.json
│   ├── topic3_germany_visa.md              # Topic 3: Germany Chancenkarte / Visa (60s Tamil)
│   └── topic3_germany_visa.json
├── docs/
│   ├── tamil_reel_script_agent_prompt.md   # Original assignment specification prompt
│   ├── implementation_plan.md              # Detailed architecture and implementation plan
│   └── code_improvement_plan.md            # Refactoring, hardening & API enhancement plan
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── research_agent.py               # Step 1: Web search, facts & content angle
│   │   ├── script_agent.py                 # Step 2: Hooks, timed script & production notes
│   │   └── quality_agent.py                # Step 3: 5-criteria audit & auto-correction
│   ├── config.py                           # Defaults, word count ranges & LLM config
│   ├── models.py                           # Pydantic schemas, regex word counter & serializers
│   ├── prompts.py                          # Dedicated system prompts for the 3 steps
│   ├── search_tool.py                      # Anti-hallucination web search abstraction
│   ├── llm.py                              # Unified LLM client (Gemini / Anthropic / OpenAI / Groq)
│   └── pipeline.py                         # Master 3-step orchestrator & regeneration controller
├── tests/
│   ├── conftest.py                         # Pytest configuration
│   └── test_pipeline.py                    # Unit and integration test suite
├── api.py                                  # FastAPI REST application with CORS & schemas
├── app.py                                  # Streamlit interactive web dashboard
├── main.py                                 # Server entrypoint: boots Uvicorn ASGI server
├── run_samples.py                          # Batch generator for the 3 sample deliverables
├── requirements.txt                        # Clean dependency specifications
├── pytest.ini                              # Pytest path settings
├── .env.example                            # Template for API keys
└── README.md                               # Project documentation
```

---

## 🚀 Quick Start

### 1. Environment Setup

Activate the virtual environment:
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

*(Or create and install dependencies afresh)*:
```bash
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

### 2. Configure API Keys
Configure your preferred provider (`gemini`, `anthropic`, or `openai`) in `.env`:
```env
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-3.8-flash
GEMINI_API_KEY=your_gemini_api_key_here
```
> **Note:** If no API key is configured, the agent runs in **Smart Simulation Mode**, generating fully compliant, calibrated scripts with live DuckDuckGo web search results.

---

## 🌐 Running the RESTful API Server (FastAPI)

Start the backend server using either:

```bash
# Option 1: Direct Python entrypoint
python main.py

# Option 2: Direct Uvicorn command
uvicorn api:app --reload --port 8000
```

Once running, the backend server is live on `http://localhost:8000`:
* **Interactive Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc Schema:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🎬 Running the Web Dashboard (Streamlit)

For an interactive browser UI to generate, inspect, regenerate hooks/CTAs, and download scripts:

```bash
python -m streamlit run app.py
```

The web dashboard will automatically open at:
* **Studio URL:** [http://localhost:8501](http://localhost:8501)

---

## 📡 API Endpoints & Usage

### 1. Health Check
* **`GET /api/v1/health`**
```bash
curl -X GET http://localhost:8000/api/v1/health
```

### 2. Generate Full Script
* **`POST /api/v1/scripts/generate`**
```bash
curl -X POST http://localhost:8000/api/v1/scripts/generate \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Why are businesses not getting leads from their websites?",
    "duration": 30,
    "tone": "Tanglish",
    "objective": "Get agency leads"
  }'
```

### 3. Regenerate Hooks Only
* **`POST /api/v1/scripts/regenerate-hook`**
```bash
curl -X POST http://localhost:8000/api/v1/scripts/regenerate-hook \
  -H "Content-Type: application/json" \
  -d '{
    "deliverable": <EXISTING_DELIVERABLE_JSON>
  }'
```

### 4. Regenerate CTA Only
* **`POST /api/v1/scripts/regenerate-cta`**
```bash
curl -X POST http://localhost:8000/api/v1/scripts/regenerate-cta \
  -H "Content-Type: application/json" \
  -d '{
    "deliverable": <EXISTING_DELIVERABLE_JSON>,
    "new_objective": "Get WhatsApp inquiries"
  }'
```

### Batch Generate Assignment Deliverables
To generate all 3 sample deliverables (`.md` and `.json`) via the core pipeline:
```bash
python run_samples.py
```

---

## 🧪 Testing

Run the test suite with pytest:
```bash
pytest tests/ -v
```

All 5 core tests verify:
* Word count cleaning excluding bullet numbers.
* Non-greedy JSON code fence parsing.
* State serialization and round-trip reloading.
* Search tool anti-hallucination behavior.
* FastAPI health and generation endpoint responses.

---

## ⚡ Token Consumption, Free Tier Limits & Commercial API Efficiency

This section provides an analysis of token economics, free-tier quotas, and commercial (paid) efficiency for the Tamil Reel Script Agent when running on **Google Gemini**.

### 1. Token Consumption Breakdown (Per Full Script Run)

A full execution performs **3 sequential LLM calls** (Research ➔ Scriptwriting ➔ Quality Check):

| Pipeline Stage | Input Content | Est. Input Tokens | Est. Output Tokens | Total Tokens |
| :--- | :--- | :---: | :---: | :---: |
| **Step 1: Research Agent** | System Prompt + Live DuckDuckGo search snippets (10–12 citations) | ~1,200 – 1,450 | ~350 – 450 | ~1,600 – 1,900 |
| **Step 2: Scriptwriting Agent** | System Prompt + Verified facts + Target duration & tone rules | ~850 – 950 | ~450 – 600 | ~1,300 – 1,550 |
| **Step 3: Quality Compliance Agent** | System Prompt + Draft script + 5 audit criteria | ~850 – 950 | ~350 – 500 | ~1,200 – 1,450 |
| **TOTAL PER SCRIPT RUN** | **All 3 steps combined** | **~2,900 – 3,350** | **~1,150 – 1,550** | **~4,100 – 4,900 tokens** |

> **Single-Feature Regenerations:**
> * `regenerate_hook`: Consumes only **~750 tokens** total (Step 2 hook regeneration + Step 3 QC re-audit).
> * `regenerate_cta`: Consumes only **~650 tokens** total (Step 2 CTA regeneration + Step 3 QC re-audit).

---

### 2. Free-Tier Quota & Limits (Google AI Studio)

The free tier for **Gemini Flash** (`gemini-3.8-flash`, `gemini-3.6-flash`, `gemini-3.5-flash-lite`, `gemini-2.5-flash`) provides generous developer limits:

| Quota Metric | Free Tier Limit | Real-World Agent Capacity |
| :--- | :---: | :--- |
| **RPM (Requests Per Minute)** | **15 RPM** | Allows **up to 5 full scripts generated per minute** simultaneously. |
| **TPM (Tokens Per Minute)** | **1,000,000 TPM** | Easily accommodates over **200+ scripts/minute** in pure token volume. |
| **RPD (Requests Per Day)** | **1,500 RPD** | Allows **up to 500 complete research-backed scripts every day for $0!** |
| **Credit Card Required?** | **No** | Instant access via [Google AI Studio](https://aistudio.google.com/apikey). |

#### Free-Tier Trade-offs:
* **Demand Spikes:** During peak global hours, the flagship model (`gemini-3.8-flash`) may temporarily return `503 UNAVAILABLE` (our codebase automatically fails over to `gemini-3.6-flash` or `gemini-3.5-flash-lite` to mitigate this).
* **Training Policy:** Under Google's free-tier terms of service, prompt inputs and outputs may be used by Google to tune and improve models.

---

### 3. Commercial (Paid) Tier: Cost & Performance Efficiency

If you upgrade to the **Pay-As-You-Go** plan (via Google Cloud Vertex AI or AI Studio Paid Billing), the agent becomes dramatically faster, more resilient, and enterprise-grade:

#### A. Extreme Cost Efficiency
Gemini Flash is one of the most cost-effective frontier models in the world:
* **Input Tokens:** ~$0.075 to $0.15 per 1,000,000 tokens
* **Output Tokens:** ~$0.30 to $0.60 per 1,000,000 tokens

#### B. Cost Breakdown Per Script:
* **Input Cost:** 3,100 tokens × $0.0000001 = **$0.00031**
* **Output Cost:** 1,350 tokens × $0.0000004 = **$0.00054**
* **Total Cost per Script:** **~$0.00085 USD (~₹0.07 INR / 7 paise per script!)**

> 💡 **Cost Takeaway:** Generating **1,000 complete video scripts** costs **less than $0.90 USD (approx. ₹75 INR)**.

#### C. Operational Advantages of Paid API:
1. **Zero 503 Traffic Errors:** Dedicated enterprise compute with a **99.9% uptime SLA**—never encounters "model temporarily busy".
2. **Massive Concurrency:** Up to **1,000+ RPM**, enabling automated content pipelines that generate hundreds of scripts in parallel.
3. **Sub-2-Second Latency:** Ultra-low latency responses with priority queuing.
4. **100% Data Confidentiality:** Paid tier guarantees that zero client data, proprietary scripts, or topics are ever logged or used to train Google's models.

---

## 📋 Standard Output Format (Strict 6 Sections + QC)

Every output produced strictly includes:
1. **Topic & Audience:** Echoes input parameters, defaults assumed, and target persona.
2. **Research Summary:** 3–5 verified findings + chosen content angle and reasoning.
3. **Hook Options:** 3 hooks (question, bold statement, pain-point) with one `[RECOMMENDED]`.
4. **Full Tamil Script:** Labeled `[Hook]`, `[Context]`, `[Body]`, `[Engagement]`, `[CTA]` with word count.
5. **Production Notes:** 3–5 on-screen text overlays, caption with hashtags, estimated duration.
6. **Sources:** URLs mapped to supported claims + `Uncertainty / Verify` alerts for official rules.
7. **Quality Check Result:** Pass/Flag audit on 5 criteria + auto-correction log.

---

## 📊 Sample Deliverables

Check the pre-generated deliverables in the [`deliverables/`](deliverables/) directory:
* [Topic 1: Website Leads (30s, Tanglish)](deliverables/topic1_website_leads.md) | [State JSON](deliverables/topic1_website_leads.json)
* [Topic 2: SEO Mistakes (45s, Tanglish)](deliverables/topic2_seo_mistakes.md) | [State JSON](deliverables/topic2_seo_mistakes.json)
* [Topic 3: Germany Opportunity Card (60s, Spoken Tamil Script)](deliverables/topic3_germany_visa.md) | [State JSON](deliverables/topic3_germany_visa.json)
