# Tamil Reel Script Agent — Code Improvement & Refactoring Plan

**Target System:** Tamil Reel Script Agent (VG Digital Falcon)  
**Goal:** Transform the codebase into a clean, simple, production-grade agent with zero mock bloat, stateful regeneration, strict anti-hallucination compliance, free-tier prototype API support, and a **RESTful API (FastAPI)** for seamless frontend integration.

---

## 1. Overview of Proposed Improvements

| Component | Current State | Target Refactored State |
| :--- | :--- | :--- |
| **Application Interface** | Terminal CLI only (`main.py` using `argparse`). | **RESTful API (FastAPI)** with CORS, OpenAPI/Swagger docs, and JSON payloads for seamless web/mobile frontend integration (React, Next.js, etc.). |
| **Simulation / Mock Bloat** | ~150 lines of static hardcoded scripts in `script_agent.py` and `research_agent.py`. | Agents contain **only** prompt orchestration and model interaction. Mocks are separated or replaced with explicit API validation. |
| **Regeneration Modes** | CLI re-runs the entire pipeline (search, scriptwriting, QC) from scratch before regenerating. | Deliverables save both `.json` (state) and `.md`. API and CLI accept deliverable state to reuse research instantly. |
| **Search Anti-Hallucination** | Injects fake URL `https://official.info/verify` when search fails. | Returns `[]` or clear `"Search unavailable"`; research agent marks findings as unverified. |
| **Agent State Mutation** | `QualityAgent.execute()` mutates input `draft` in place. | `QualityAgent` returns `Tuple[QualityCheckResult, ScriptDraft]`, ensuring pure data flow. |
| **LLM Provider Support** | `GEMINI_API_KEY` defined in config but unhandled in `llm.py`; greedy regex JSON parsing. | Native **Gemini 1.5/2.0 Flash** integration via `google-genai` / Groq OpenAI compatibility; non-greedy JSON parser. |
| **Pacing / Word Count** | Counts punctuation and bullet numbers (`"1."`) as spoken words. | Regex-based spoken token cleaner for Tamil script and Tanglish. |
| **Code Cleanliness** | Duplicated UTF-8 Windows boilerplate; absolute hardcoded paths in `README.md`. | Consolidated UTF-8 helper, relative markdown links throughout. |

---

## 2. Detailed Component Changes

### 2.1. Hardening Search Tool (`src/search_tool.py`)
**Problem:** Generating fake fallback URLs violates the zero-hallucination mandate.  
**Fix:** On error or zero results, log a warning and return an empty list.

```python
"""Web search tool using DuckDuckGo for live reputable research."""

import logging
import warnings
from typing import List, Dict

warnings.filterwarnings("ignore", category=RuntimeWarning, module="duckduckgo_search")
logger = logging.getLogger(__name__)


def search_web(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Execute a web search query and return formatted results.
    
    Returns an empty list on failure to prevent hallucinated URLs.
    """
    results = []
    try:
        from duckduckgo_search import DDGS

        ddgs = DDGS()
        raw_results = list(ddgs.text(query, max_results=max_results))
        for item in raw_results:
            url = item.get("href") or item.get("link") or ""
            if url:
                results.append({
                    "title": item.get("title", "Source"),
                    "url": url,
                    "snippet": item.get("body", "").strip(),
                })
    except Exception as e:
        logger.warning(f"DuckDuckGo search error for query '{query}': {e}")
        # Return empty list — never invent fake URLs like 'https://official.info/verify'
        return []

    return results
```

---

### 2.2. Enhancing `src/models.py` with State Persistence & Clean Word Counting

**Problem:**
1. Word count counts `"1."` and punctuation tokens.
2. No serialization methods to reload existing deliverables for regeneration.

**Fix:**
```python
import re
from pathlib import Path
from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field
from src.config import (
    DEFAULT_PLATFORM,
    DEFAULT_DURATION,
    DEFAULT_TONE,
    DEFAULT_OBJECTIVE,
    DEFAULT_MODE,
    WORD_COUNT_LIMITS,
)


class ScriptDraft(BaseModel):
    hooks: List["HookItem"] = Field(default_factory=list)
    hook: str = ""
    context: str = ""
    body_points: List[str] = Field(default_factory=list)
    engagement: str = ""
    cta: str = ""
    word_count: int = 0
    on_screen_texts: List[str] = Field(default_factory=list)
    caption: str = ""
    hashtags: List[str] = Field(default_factory=list)
    estimated_duration: str = ""

    def calculate_word_count(self) -> int:
        """Calculate pure spoken words across all script segments, excluding bullet numbers."""
        # Strip leading numbers like '1. ', '2. '
        cleaned_points = [re.sub(r"^\d+[\.\)]\s*", "", p) for p in self.body_points]
        raw_text = f"{self.hook} {self.context} {' '.join(cleaned_points)} {self.engagement} {self.cta}"
        # Extract unicode words (handles both Latin Tanglish and Tamil Unicode)
        tokens = re.findall(r"\b[\w\-']+\b", raw_text, flags=re.UNICODE)
        return len(tokens)


class FullDeliverable(BaseModel):
    input_data: ScriptInput
    research: ResearchResult
    script: ScriptDraft
    quality_check: QualityCheckResult

    def save_deliverables(self, base_path: Path):
        """Save both human-readable Markdown and machine-readable JSON."""
        base_path.parent.mkdir(parents=True, exist_ok=True)
        # Markdown
        md_file = base_path.with_suffix(".md")
        md_file.write_text(self.to_markdown(), encoding="utf-8")
        # JSON (State file for regeneration)
        json_file = base_path.with_suffix(".json")
        json_file.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load_from_json(cls, json_path: Path) -> "FullDeliverable":
        return cls.model_validate_json(json_path.read_text(encoding="utf-8"))
```

---

### 2.3. Clean LLM Client with Gemini & Groq Support (`src/llm.py`)

**Problem:** `GEMINI_API_KEY` was ignored; `clean_json_response` used greedy regex.  
**Fix:** Add native Google Gemini support (via `google-genai` or standard SDK), add Groq / OpenAI compatible base URL support, and improve JSON fence extraction.

```python
"""Unified LLM client interface supporting Gemini, Anthropic, OpenAI/Groq."""

import json
import logging
import re
from typing import Dict, Any, Optional
import os
from src.config import (
    LLM_PROVIDER,
    ANTHROPIC_API_KEY,
    OPENAI_API_KEY,
    GEMINI_API_KEY,
    ANTHROPIC_MODEL,
    OPENAI_MODEL,
)

logger = logging.getLogger(__name__)


def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Clean markdown code fences and parse JSON safely using non-greedy extraction."""
    text = raw_text.strip()
    
    # 1. Direct parse attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Extract ```json ... ``` code fence (non-greedy)
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # 3. Fallback: extract from first { to last }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to parse LLM response as JSON. Output was:\n{raw_text}")


class LLMClient:
    """Unified LLM caller that routes to Gemini, Anthropic, or OpenAI/Groq."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or LLM_PROVIDER).lower()
        self.gemini_client = None
        self.anthropic_client = None
        self.openai_client = None

        # 1. Google Gemini (Ideal for free prototype)
        if GEMINI_API_KEY and self.provider in ("gemini", "auto"):
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                self.provider = "gemini"
            except ImportError:
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=GEMINI_API_KEY)
                    self.gemini_client = genai.GenerativeModel("gemini-1.5-flash")
                    self.provider = "gemini"
                except Exception as e:
                    logger.warning(f"Could not initialize Gemini: {e}")

        # 2. Anthropic
        if not self.gemini_client and ANTHROPIC_API_KEY and self.provider in ("anthropic", "auto"):
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                self.provider = "anthropic"
            except Exception as e:
                logger.warning(f"Could not initialize Anthropic: {e}")

        # 3. OpenAI / Groq Compatible
        if not self.gemini_client and not self.anthropic_client and OPENAI_API_KEY and self.provider in ("openai", "groq", "auto"):
            try:
                import openai
                base_url = os.getenv("OPENAI_BASE_URL", None)  # Allows Groq endpoint: https://api.groq.com/openai/v1
                self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url=base_url)
                self.provider = "openai"
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI/Groq: {e}")

        if not any([self.gemini_client, self.anthropic_client, self.openai_client]):
            logger.warning("No active LLM API keys detected. Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY in .env.")

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Invoke LLM and return parsed JSON object."""
        if self.provider == "gemini" and self.gemini_client:
            combined_prompt = f"{system_prompt}\n\nUSER REQUEST:\n{user_prompt}\n\nOutput strictly valid JSON only."
            if hasattr(self.gemini_client, "models"):  # google-genai SDK
                response = self.gemini_client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=combined_prompt,
                )
                return clean_json_response(response.text)
            else:  # google.generativeai legacy SDK
                response = self.gemini_client.generate_content(combined_prompt)
                return clean_json_response(response.text)

        elif self.provider == "anthropic" and self.anthropic_client:
            response = self.anthropic_client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=2500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return clean_json_response(response.content[0].text)

        elif self.provider in ("openai", "groq") and self.openai_client:
            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return clean_json_response(response.choices[0].message.content)

        raise RuntimeError(f"No configured LLM provider available for '{self.provider}'. Please check .env configuration.")
```

---

### 2.4. Streamlining `ScriptAgent` (Eliminating Hardcoded Fallbacks)

**Problem:** `src/agents/script_agent.py` was bloated with 120 lines of static copy.  
**Fix:** Keep `ScriptAgent` focused purely on prompt generation, calling LLM, and parsing into `ScriptDraft`.

```python
"""Step 2: Scriptwriter Agent for Hooks, Scriptwriting, and Production Notes."""

import logging
from src.models import ScriptInput, ResearchResult, ScriptDraft, HookItem
from src.config import WORD_COUNT_LIMITS
from src.prompts import SCRIPT_SYSTEM_PROMPT, REGENERATE_HOOK_PROMPT, REGENERATE_CTA_PROMPT
from src.llm import LLMClient

logger = logging.getLogger(__name__)


class ScriptAgent:
    """Generates 3 hook options, timed spoken script, and production notes."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def execute(self, inp: ScriptInput, research: ResearchResult) -> ScriptDraft:
        limits = WORD_COUNT_LIMITS.get(inp.duration, {"min": 60, "max": 75, "target": 68})

        user_prompt = f"""Topic: {inp.topic}
Audience: {inp.audience}
Platform: {inp.platform}
Target Duration: {inp.duration} seconds (STRICT word count: {limits['min']}-{limits['max']} words)
Tone: {inp.tone}
Objective: {inp.objective}

RESEARCH FINDINGS:
{chr(10).join(f"- {f}" for f in research.key_findings)}

CHOSEN CONTENT ANGLE:
{research.chosen_angle} (Reason: {research.angle_reason})

PAIN POINTS:
{chr(10).join(f"- {p}" for p in research.pain_points)}

Write the script following all duration, pacing, and tone rules strictly. Ensure pure spoken words are between {limits['min']} and {limits['max']} words!
"""
        data = self.llm.generate_json(system_prompt=SCRIPT_SYSTEM_PROMPT, user_prompt=user_prompt)

        hooks_list = [
            HookItem(
                text=h.get("text", ""),
                type=h.get("type", "bold statement"),
                is_recommended=h.get("is_recommended", False),
                reason=h.get("reason", ""),
            )
            for h in data.get("hooks", [])
        ]

        if hooks_list and not any(h.is_recommended for h in hooks_list):
            hooks_list[0].is_recommended = True
            hooks_list[0].reason = "Selected as primary hook."

        active_hook = data.get("hook") or (hooks_list[0].text if hooks_list else "")

        draft = ScriptDraft(
            hooks=hooks_list,
            hook=active_hook,
            context=data.get("context", ""),
            body_points=data.get("body_points", []),
            engagement=data.get("engagement", ""),
            cta=data.get("cta", ""),
            on_screen_texts=data.get("on_screen_texts", []),
            caption=data.get("caption", ""),
            hashtags=data.get("hashtags", []),
            estimated_duration=data.get("estimated_duration", f"{inp.duration} sec"),
        )
        draft.word_count = draft.calculate_word_count()
        return draft
```

---

### 2.5. Refactoring `QualityAgent` to Avoid In-Place Side Effects

**Problem:** `QualityAgent.execute()` mutates `draft` in place.  
**Fix:** Return `Tuple[QualityCheckResult, ScriptDraft]`.

```python
"""Step 3: Quality Check and Self-Correction Agent."""

from typing import Tuple
from src.models import ScriptInput, ResearchResult, ScriptDraft, QualityCheckResult, CheckItem
from src.config import WORD_COUNT_LIMITS
from src.prompts import QUALITY_CHECK_SYSTEM_PROMPT
from src.llm import LLMClient


class QualityAgent:
    """Rigorous 5-point quality auditor with automatic self-correction."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def execute(self, inp: ScriptInput, research: ResearchResult, draft: ScriptDraft) -> Tuple[QualityCheckResult, ScriptDraft]:
        limits = WORD_COUNT_LIMITS.get(inp.duration, {"min": 60, "max": 75})
        actual_words = draft.calculate_word_count()

        user_prompt = f"""Topic: {inp.topic}
Audience: {inp.audience}
Duration: {inp.duration}s (Target: {limits['min']}-{limits['max']} words | Actual: {actual_words} words)
Tone: {inp.tone}
Objective: {inp.objective}

RESEARCH SOURCES:
{chr(10).join(f"- {s.claim_supported} ({s.url})" for s in research.sources)}

DRAFT SCRIPT TO AUDIT:
[Hook] {draft.hook}
[Context] {draft.context}
[Body]
{chr(10).join(f"- {p}" for p in draft.body_points)}
[Engagement] {draft.engagement}
[CTA] {draft.cta}

Perform the 5-point quality audit. If any criteria is flagged, you MUST provide the corrected script under 'revised_script'.
"""
        data = self.llm.generate_json(system_prompt=QUALITY_CHECK_SYSTEM_PROMPT, user_prompt=user_prompt)

        checks_data = data.get("checks", {})
        fixes_applied = data.get("fixes_applied", [])
        revised = data.get("revised_script")

        # Create updated draft copy without mutating original
        updated_draft = draft.model_copy(deep=True)
        if revised and isinstance(revised, dict):
            if revised.get("hook"):
                updated_draft.hook = revised["hook"]
            if revised.get("context"):
                updated_draft.context = revised["context"]
            if revised.get("body_points"):
                updated_draft.body_points = revised["body_points"]
            if revised.get("engagement"):
                updated_draft.engagement = revised["engagement"]
            if revised.get("cta"):
                updated_draft.cta = revised["cta"]
            updated_draft.word_count = updated_draft.calculate_word_count()

        qc_result = QualityCheckResult(
            unsupported_claims=CheckItem(
                status=checks_data.get("unsupported_claims", {}).get("status", "PASS"),
                notes=checks_data.get("unsupported_claims", {}).get("notes", "Verified."),
            ),
            repetition=CheckItem(
                status=checks_data.get("repetition", {}).get("status", "PASS"),
                notes=checks_data.get("repetition", {}).get("notes", "No repetition found."),
            ),
            weak_cta=CheckItem(
                status=checks_data.get("weak_cta", {}).get("status", "PASS"),
                notes=checks_data.get("weak_cta", {}).get("notes", "Specific and aligned."),
            ),
            unnatural_tamil=CheckItem(
                status=checks_data.get("unnatural_tamil", {}).get("status", "PASS"),
                notes=checks_data.get("unnatural_tamil", {}).get("notes", "Natural spoken phrasing."),
            ),
            duration_fit=CheckItem(
                status=checks_data.get("duration_fit", {}).get("status", "PASS"),
                notes=checks_data.get("duration_fit", {}).get("notes", f"Calibrated ({updated_draft.word_count}w)."),
            ),
            fixes_applied=fixes_applied,
        )

        return qc_result, updated_draft
```

---

### 2.6. CLI Upgrade for Persistent Regeneration (`main.py`)

**Problem:** CLI did not support loading prior deliverable JSON files for `--mode regenerate_hook` or `regenerate_cta`.  
**Fix:** Add `--from-deliverable` argument.

```python
    parser.add_argument(
        "--from-deliverable",
        help="Path to an existing .json deliverable to reuse research/body for hook or CTA regeneration",
    )
```

In `main()`:
```python
    prev_deliverable = None
    if args.from_deliverable:
        json_path = Path(args.from_deliverable)
        if not json_path.exists():
            raise FileNotFoundError(f"Deliverable file not found: {json_path}")
        prev_deliverable = FullDeliverable.load_from_json(json_path)

    deliverable = pipeline.run(inp, previous_deliverable=prev_deliverable)

    # Save outputs if specified (both .md and .json)
    if args.output:
        out_base = Path(args.output)
        deliverable.save_deliverables(out_base)
        print(f"\n[SAVED] Markdown: {out_base.with_suffix('.md')}")
        print(f"[SAVED] State JSON: {out_base.with_suffix('.json')}")
```

---

### 2.7. RESTful API Backend (FastAPI) for Frontend Integration

**Problem:** Currently, inputs can only be entered manually via the terminal (`main.py`). Modern video production workflows require a web dashboard (e.g. Next.js, React, or mobile app) where creators or marketing teams can input a topic, view real-time research, choose hook variations, preview the script, and click "Regenerate".

**Solution:** Expose the pipeline as a lightweight **RESTful API** using **FastAPI**. Because our data models (`ScriptInput`, `FullDeliverable`, `ScriptDraft`, etc.) are already built with **Pydantic v2**, FastAPI works out of the box with zero boilerplate, providing:
1. Automatic input validation and error responses (`422 Unprocessable Entity`).
2. Interactive OpenAPI / Swagger UI at `/docs`.
3. Cross-Origin Resource Sharing (CORS) for local and deployed frontends.
4. Seamless JSON payloads matching the frontend state.

#### A. New API Service Implementation (`api.py`)

Create `api.py` in the project root:

```python
"""FastAPI REST service for the Tamil Reel Script Agent.

Enables seamless integration with React, Next.js, or mobile frontends.
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from src.models import ScriptInput, FullDeliverable
from src.pipeline import TamilReelScriptPipeline
from src.config import LLM_PROVIDER

app = FastAPI(
    title="Tamil Reel Script Agent API",
    description="RESTful API for research-backed Tamil & Tanglish short-form video script generation.",
    version="1.0.0",
)

# Enable CORS for frontend clients (React, Next.js, Vite, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust to specific domains in production (e.g., ["http://localhost:3000"])
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = TamilReelScriptPipeline()


class GenerateResponse(BaseModel):
    success: bool
    deliverable: FullDeliverable
    markdown: str


class RegenerateHookRequest(BaseModel):
    deliverable: FullDeliverable


class RegenerateCtaRequest(BaseModel):
    deliverable: FullDeliverable
    new_objective: Optional[str] = None


@app.get("/api/v1/health", tags=["System"])
def health_check():
    """Verify backend health and active LLM configuration."""
    return {
        "status": "healthy",
        "active_provider": LLM_PROVIDER,
        "service": "Tamil Reel Script Agent",
    }


@app.post(
    "/api/v1/scripts/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Script Generation"],
)
def generate_full_script(payload: ScriptInput):
    """Generate a complete 6-section research-backed script deliverable."""
    try:
        # Ensure mode is set to full_script
        payload.mode = "full_script"
        deliverable = pipeline.run(payload)
        return GenerateResponse(
            success=True,
            deliverable=deliverable,
            markdown=deliverable.to_markdown(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline generation failed: {str(e)}",
        )


@app.post(
    "/api/v1/scripts/regenerate-hook",
    response_model=GenerateResponse,
    tags=["Regeneration"],
)
def regenerate_hook(payload: RegenerateHookRequest):
    """Regenerate 3 new hook options without re-searching or rewriting the body."""
    try:
        inp = payload.deliverable.input_data
        inp.mode = "regenerate_hook"
        updated = pipeline.run(inp, previous_deliverable=payload.deliverable)
        return GenerateResponse(
            success=True,
            deliverable=updated,
            markdown=updated.to_markdown(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Hook regeneration failed: {str(e)}",
        )


@app.post(
    "/api/v1/scripts/regenerate-cta",
    response_model=GenerateResponse,
    tags=["Regeneration"],
)
def regenerate_cta(payload: RegenerateCtaRequest):
    """Regenerate 3 new CTA options matching the objective."""
    try:
        inp = payload.deliverable.input_data
        if payload.new_objective:
            inp.objective = payload.new_objective
        inp.mode = "regenerate_cta"
        updated = pipeline.run(inp, previous_deliverable=payload.deliverable)
        return GenerateResponse(
            success=True,
            deliverable=updated,
            markdown=updated.to_markdown(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CTA regeneration failed: {str(e)}",
        )
```

#### B. Running the REST API Server

Add `fastapi` and `uvicorn` to `requirements.txt`:
```bash
pip install fastapi uvicorn
```

Launch the development server:
```bash
uvicorn api:app --reload --port 8000
```
* **Interactive Docs:** Visit `http://localhost:8000/docs` to test all endpoints via Swagger UI.

#### C. Frontend Integration Example (Next.js / React)

A frontend component can trigger script generation with standard `fetch` or `axios`:

```typescript
// Example: React / Next.js API Call
async function generateTamilReel(topic: string, duration: number, tone: string) {
  const response = await fetch("http://localhost:8000/api/v1/scripts/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      topic: topic,
      duration: duration, // 30, 45, or 60
      tone: tone,         // "Tanglish" or "conversational spoken Tamil"
      platform: "Instagram Reels",
      objective: "Get agency leads"
    }),
  });

  const data = await response.json();
  console.log("Hooks:", data.deliverable.script.hooks);
  console.log("Full Script:", data.markdown);
  return data.deliverable;
}
```

---

## 3. Testing and Verification Strategy


Create `tests/test_pipeline.py` with lightweight unit tests:
1. `test_word_count_calculation`: Confirms numbered points `"1. Hero"` don't skew word counts.
2. `test_clean_json_response`: Tests non-greedy extraction with surrounding text.
3. `test_deliverable_serialization`: Verifies `.save_deliverables()` and `.load_from_json()` round-trip fidelity.
4. `test_search_tool_handles_failures`: Confirms zero fake URLs on network error.

---

## 4. Documentation Fixes in `README.md`

Replace:
```markdown
* [Topic 1: Website Leads (30s, Tanglish)](file:///c:/Users/kuber/Tamil-reel-script-agent/deliverables/topic1_website_leads.md)
```
With clean relative links:
```markdown
* [Topic 1: Website Leads (30s, Tanglish)](deliverables/topic1_website_leads.md)
* [Topic 2: SEO Mistakes (45s, Tanglish)](deliverables/topic2_seo_mistakes.md)
* [Topic 3: Germany Opportunity Card (60s, Spoken Tamil Script)](deliverables/topic3_germany_visa.md)
```
