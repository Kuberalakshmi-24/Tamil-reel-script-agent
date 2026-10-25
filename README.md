# Tamil Reel Script Agent (VG Digital Falcon)

An automated short-form video content agent that transforms any topic into a research-backed, viral, ready-to-record video script for **Instagram Reels**, **YouTube Shorts**, and **Facebook Reels** in spoken colloquial Tamil or Tanglish.

---

## 🌟 Key Features

1. **3-Step Code Pipeline (Separation of Concerns):**
   * **Step 1 (Research Agent):** Executes 3–6 live web searches via DuckDuckGo, extracts verified facts and audience pain points with URLs, and selects one actionable content angle.
   * **Step 2 (Scriptwriting Agent):** Crafts 3 distinct hooks ($\le 12$ words each: question, bold statement, pain-point), a structured spoken script (`[Hook] -> [Context] -> [Body] -> [Engagement] -> [CTA]`), and production notes (on-screen text, caption, hashtags).
   * **Step 3 (Quality Auditor & Self-Correction):** Audits draft against 5 strict quality criteria (unsupported claims, repetition, weak CTA, unnatural Tamil, and duration fit) and automatically applies self-correcting revisions before delivery.
2. **Spoken Pacing Calibration:**
   * Calibrated for spoken Tamil/Tanglish at **~2.2 words/second**:
     * **30 sec:** 60 – 75 words
     * **45 sec:** 95 – 110 words
     * **60 sec:** 125 – 145 words
3. **Regeneration Modes:**
   * `regenerate_hook`: Reuses existing research and body; generates 3 fresh hooks without re-searching.
   * `regenerate_cta`: Reuses existing research and body; generates 3 fresh, high-converting CTAs.
4. **Safety & Zero Hallucination:**
   * Every factual claim maps to a live source URL.
   * Time-sensitive or official visa/legal rules automatically append verification notices.

---

## 📁 Project Structure

```text
Tamil-reel-script-agent/
├── deliverables/                           # 3 sample deliverables required by specification
│   ├── topic1_website_leads.md             # Topic 1: Business leads from websites (30s Tanglish)
│   ├── topic2_seo_mistakes.md              # Topic 2: Common SEO mistakes (45s Tanglish)
│   └── topic3_germany_visa.md              # Topic 3: Germany Chancenkarte / Visa (60s Tamil)
├── docs/
│   ├── tamil_reel_script_agent_prompt.md   # Original assignment specification prompt
│   └── implementation_plan.md              # Detailed architecture and implementation plan
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── research_agent.py               # Step 1: Web search, facts & content angle
│   │   ├── script_agent.py                 # Step 2: Hooks, timed script & production notes
│   │   └── quality_agent.py                # Step 3: 5-criteria audit & auto-correction
│   ├── config.py                           # Defaults, word count ranges & LLM config
│   ├── models.py                           # Pydantic schemas & Markdown serializer
│   ├── prompts.py                          # Dedicated system prompts for the 3 steps
│   ├── search_tool.py                      # DuckDuckGo live search abstraction
│   ├── llm.py                              # Unified LLM client (Anthropic / OpenAI / Smart Simulation)
│   └── pipeline.py                         # Master 3-step orchestrator & regeneration controller
├── main.py                                 # Single-topic CLI interface
├── run_samples.py                          # Batch generator for the 3 sample deliverables
├── requirements.txt                        # Clean dependency specifications
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

*(Or create and install afresh)*:
```bash
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

### 2. Configure API Keys (Optional)
Copy `.env.example` to `.env` and insert your Claude or OpenAI API key:
```bash
cp .env.example .env
```
> **Note:** If no API key is configured, the agent runs in **Smart Simulation Mode**, generating fully compliant, calibrated scripts with live DuckDuckGo web search results.

---

## 🛠️ Usage

### Generate All 3 Assignment Deliverables
To run the automated pipeline across the 3 test topics and save outputs to `deliverables/`:
```bash
python run_samples.py
```

### Run Custom Topic via CLI
Generate a full script with custom parameters:
```bash
python main.py --topic "Why are businesses not getting leads from their websites?" --duration 30 --tone Tanglish --objective "Get agency leads"
```

Save output directly to a file:
```bash
python main.py --topic "Common SEO mistakes for small business" --duration 45 --output deliverables/my_seo_reel.md
```

### Regenerate Hooks Only
Swap hooks without re-running web searches:
```bash
python main.py --topic "Why are businesses not getting leads from their websites?" --mode regenerate_hook
```

### Regenerate CTA Only
Swap the Call-To-Action to test conversion variations:
```bash
python main.py --topic "Why are businesses not getting leads from their websites?" --mode regenerate_cta
```

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

Check the pre-generated deliverables in the [`deliverables/`](file:///c:/Users/kuber/Tamil-reel-script-agent/deliverables/) directory:
* [Topic 1: Website Leads (30s, Tanglish)](file:///c:/Users/kuber/Tamil-reel-script-agent/deliverables/topic1_website_leads.md)
* [Topic 2: SEO Mistakes (45s, Tanglish)](file:///c:/Users/kuber/Tamil-reel-script-agent/deliverables/topic2_seo_mistakes.md)
* [Topic 3: Germany Opportunity Card (60s, Spoken Tamil Script)](file:///c:/Users/kuber/Tamil-reel-script-agent/deliverables/topic3_germany_visa.md)
