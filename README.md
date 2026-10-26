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
GEMINI_MODEL=gemini-3.5-flash
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
