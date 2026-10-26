# Tamil Reel Script Agent — Fixes & Enhancement Specification

This document details the root causes, architecture decisions, and exact code implementations for the 10 identified defects and optimizations across the codebase.

---

## Table of Contents
1. [Fix 1: Correct Invalid Gemini Model Identifier](#1-fix-invalid-gemini-model-identifier)
2. [Fix 2: Robust Nested JSON Code-Fence Extraction](#2-fix-defective-non-greedy-regex-in-json-extraction)
3. [Fix 3: Synchronize Recommended Hook with Hook Options on Quality Revision](#3-synchronize-recommended-hook-with-hook-options-on-quality-revision)
4. [Fix 4: Preserve All Alternative CTA Options on Regeneration](#4-preserve-all-alternative-cta-options-on-regeneration)
5. [Fix 5: Restore CLI Interface with Stateful Regeneration](#5-restore-cli-interface-with-stateful-regeneration)
6. [Fix 6: Add Schema Boundaries & Pydantic Field Validation](#6-add-schema-boundaries--pydantic-field-validation)
7. [Fix 7: Graceful Error Handling for Streamlit Regeneration Buttons](#7-graceful-error-handling-for-streamlit-regeneration-buttons)
8. [Fix 8: Offline Test Mocking for Search Tool & LLM](#8-offline-test-mocking-for-search-tool--llm)
9. [Fix 9: Computed Word Count Property](#9-computed-word-count-property)
10. [Enhancement 10: Streamlit Frontend Optimization for Arbitrary Topics](#10-streamlit-frontend-optimization-for-arbitrary-topics)

---

## 1. Fix: Invalid Gemini Model Identifier

### Root Cause
In `src/config.py:33` and `src/llm.py:109`, the default Gemini model is configured as `"gemini-3.5-flash"`. This model name does not exist in the Google Gemini API (official models: `gemini-1.5-flash`, `gemini-2.0-flash`, `gemini-1.5-pro`). When `LLM_PROVIDER=gemini` is selected, Google API calls fail with a 404 (`NotFoundError`), silently triggering the fallback simulation generator without utilizing the live model.

### Code Changes

#### `src/config.py`
```python
# Before (Line 33)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# After
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
```

#### `src/llm.py`
```python
# Before (Line 109-110)
if hasattr(self.gemini_client, "models"):  # google-genai SDK
    model_name = GEMINI_MODEL or "gemini-3.5-flash"

# After
if hasattr(self.gemini_client, "models"):  # google-genai SDK
    model_name = GEMINI_MODEL or "gemini-1.5-flash"
```

---

## 2. Fix: Defective Non-Greedy Regex in JSON Extraction

### Root Cause
In `src/llm.py:32`, the regex:
```python
match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
```
uses non-greedy matching `\{.*?\}`. For any JSON structure containing nested curly braces (e.g., `QualityCheckResult`'s `"checks": { ... }` or `ResearchResult`'s `"sources": [ { ... } ]`), it terminates at the **first** closing brace `}` inside the object, producing truncated text and raising a `JSONDecodeError`.

### Code Changes

#### `src/llm.py`
```python
def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Clean markdown code fences and parse JSON safely."""
    text = raw_text.strip()

    # 1. Direct parse attempt
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Extract content within ```json ... ``` or ``` ... ``` code fence
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        fence_content = fence_match.group(1).strip()
        try:
            return json.loads(fence_content)
        except json.JSONDecodeError:
            text = fence_content  # Fall through to brace extraction on fence content

    # 3. Robust substring extraction: outermost { to outermost }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(text[first_brace : last_brace + 1])
        except json.JSONDecodeError:
            pass

    # 4. Fallback for array root if applicable
    first_bracket = text.find("[")
    last_bracket = text.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        try:
            return json.loads(text[first_bracket : last_bracket + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Failed to parse LLM response as JSON. Output was:\n{raw_text}")
```

---

## 3. Synchronize Recommended Hook with Hook Options on Quality Revision

### Root Cause
In `src/agents/quality_agent.py`, when self-correction triggers and `revised_script["hook"]` updates `updated_draft.hook`, the `updated_draft.hooks` list is not modified. Consequently:
- Section 3 ("Hook Options") shows the original recommended hook.
- Section 4 ("Full Tamil Script") shows the newly revised hook.

### Code Changes

#### `src/agents/quality_agent.py`
```python
# Lines 69-80 in execute():
updated_draft = draft.model_copy(deep=True)
if revised and isinstance(revised, dict):
    if revised.get("hook"):
        revised_hook_text = revised["hook"].strip()
        updated_draft.hook = revised_hook_text
        # Synchronize the recommended hook in the hooks list
        found_rec = False
        for h in updated_draft.hooks:
            if h.is_recommended:
                h.text = revised_hook_text
                h.reason = "Revised by Quality Auditor for tone/duration compliance."
                found_rec = True
                break
        if not found_rec and updated_draft.hooks:
            updated_draft.hooks[0].text = revised_hook_text
            updated_draft.hooks[0].is_recommended = True

    if revised.get("context"):
        updated_draft.context = revised["context"]
    if revised.get("body_points"):
        updated_draft.body_points = revised["body_points"]
    if revised.get("engagement"):
        updated_draft.engagement = revised["engagement"]
    if revised.get("cta"):
        updated_draft.cta = revised["cta"]
```

---

## 4. Preserve All Alternative CTA Options on Regeneration

### Root Cause
When `REGENERATE_CTA_PROMPT` runs, the LLM provides 3 distinct CTA options (`cta_options`). However, `ScriptDraft` only stores a single `cta: str`, discarding the alternative options.

### Code Changes

#### `src/models.py`
Add `CtaOptionItem` and store `cta_options` inside `ScriptDraft`:
```python
class CtaOptionItem(BaseModel):
    text: str
    is_recommended: bool = False
    reason: str = ""

class ScriptDraft(BaseModel):
    hooks: List[HookItem] = Field(default_factory=list)
    hook: str = ""
    context: str = ""
    body_points: List[str] = Field(default_factory=list)
    engagement: str = ""
    cta: str = ""
    cta_options: List[CtaOptionItem] = Field(default_factory=list)
    on_screen_texts: List[str] = Field(default_factory=list)
    caption: str = ""
    hashtags: List[str] = Field(default_factory=list)
    estimated_duration: str = ""
```

#### `src/agents/script_agent.py`
```python
def regenerate_cta(self, inp: ScriptInput, draft: ScriptDraft) -> ScriptDraft:
    # ... prompt execution ...
    cta_options_raw = data.get("cta_options", [])
    cta_items = [
        CtaOptionItem(
            text=c.get("text", ""),
            is_recommended=c.get("is_recommended", False),
            reason=c.get("reason", ""),
        )
        for c in cta_options_raw
    ]
    rec_cta = data.get("recommended_cta") or (cta_items[0].text if cta_items else draft.cta)

    updated_draft = draft.model_copy(deep=True)
    updated_draft.cta = rec_cta
    updated_draft.cta_options = cta_items
    return updated_draft
```

---

## 5. Restore CLI Interface with Stateful Regeneration

### Root Cause
`main.py` was replaced entirely with `uvicorn.run("api:app")`. Terminal users can no longer execute one-shot runs or regenerate hooks/CTAs from saved deliverable `.json` files via the CLI.

### Code Implementation

#### `main.py` (Unified CLI & Server Entrypoint)
```python
"""Unified CLI and Server entrypoint for Tamil Reel Script Agent."""

import argparse
import sys
from pathlib import Path

from src.utils import setup_utf8_console
setup_utf8_console()

from src.models import ScriptInput, FullDeliverable
from src.pipeline import TamilReelScriptPipeline
from src.config import DELIVERABLES_DIR


def run_cli():
    parser = argparse.ArgumentParser(
        description="Tamil Reel Script Agent: Generate and fine-tune short-form video scripts."
    )
    parser.add_argument("--topic", type=str, help="Primary topic for the reel")
    parser.add_argument("--duration", type=int, choices=[30, 45, 60], default=30, help="Target duration (sec)")
    parser.add_argument("--tone", type=str, default="Tanglish", choices=["Tanglish", "conversational spoken Tamil", "Tamil"])
    parser.add_argument("--objective", type=str, default="awareness", help="Marketing objective")
    parser.add_argument("--audience", type=str, default=None, help="Target audience description")
    parser.add_argument("--niche", type=str, default=None, help="Niche / industry category")
    parser.add_argument("--mode", type=str, default="full_script", choices=["full_script", "regenerate_hook", "regenerate_cta"])
    parser.add_argument("--from-deliverable", type=str, default=None, help="Path to existing state .json deliverable for regeneration")
    parser.add_argument("--server", action="store_true", help="Launch FastAPI REST server instead of CLI")
    parser.add_argument("--port", type=int, default=8000, help="Port for REST server (default: 8000)")

    args = parser.parse_args()

    if args.server:
        import uvicorn
        print(f">> Starting Tamil Reel Script Agent API on http://localhost:{args.port}")
        uvicorn.run("api:app", host="0.0.0.0", port=args.port, reload=True)
        return

    if not args.topic and not args.from_deliverable:
        parser.print_help()
        sys.exit(1)

    pipeline = TamilReelScriptPipeline()

    prev_deliverable = None
    if args.from_deliverable:
        json_path = Path(args.from_deliverable)
        if not json_path.exists():
            print(f"Error: Deliverable file not found at {json_path}")
            sys.exit(1)
        prev_deliverable = FullDeliverable.load_from_json(json_path)

    inp = ScriptInput.create_with_defaults(
        topic=args.topic or (prev_deliverable.input_data.topic if prev_deliverable else ""),
        audience=args.audience or (prev_deliverable.input_data.audience if prev_deliverable else None),
        niche=args.niche or (prev_deliverable.input_data.niche if prev_deliverable else None),
        duration=args.duration,
        tone=args.tone,
        objective=args.objective,
        mode=args.mode,
    )

    result = pipeline.run(inp, previous_deliverable=prev_deliverable)

    slug = inp.topic.lower()[:30].replace(" ", "_").replace("?", "")
    out_base = DELIVERABLES_DIR / f"cli_{slug}"
    result.save_deliverables(out_base)

    print("\n" + "=" * 60)
    print(result.to_markdown())
    print("=" * 60)
    print(f"\nDeliverable saved to: {out_base.with_suffix('.md')}")
    print(f"State saved to:       {out_base.with_suffix('.json')}\n")


if __name__ == "__main__":
    run_cli()
```

---

## 6. Add Schema Boundaries & Pydantic Field Validation

### Root Cause
`ScriptInput` fields were unconstrained, permitting empty topics or multi-megabyte payloads that could break prompt templates or deplete model context.

### Code Changes

#### `src/models.py`
```python
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ScriptInput(BaseModel):
    """Validated input payload for script generation."""
    topic: str = Field(..., min_length=3, max_length=300, description="Primary topic for the reel")
    audience: Optional[str] = Field(default=None, max_length=150, description="Target demographic")
    niche: Optional[str] = Field(default=None, max_length=100, description="Industry domain")
    platform: str = Field(default=DEFAULT_PLATFORM, max_length=50)
    duration: Literal[30, 45, 60] = Field(default=30, description="Target video duration in seconds")
    tone: Literal["Tanglish", "conversational spoken Tamil", "Tamil"] = Field(default="Tanglish")
    objective: str = Field(default=DEFAULT_OBJECTIVE, max_length=120)
    mode: Literal["full_script", "regenerate_hook", "regenerate_cta"] = Field(default="full_script")
    assumed_defaults: List[str] = Field(default_factory=list)
```

---

## 7. Graceful Error Handling for Streamlit Regeneration Buttons

### Root Cause
In `app.py:273-278` and `app.py:312-319`, button click callbacks invoke `pipeline.run()` without `try...except` handling, crashing the app if an API key expires or a network request drops.

### Code Changes

#### `app.py`
```python
# Hook Regeneration
if st.button("⚡ Regenerate 3 Fresh Hooks", use_container_width=True):
    with st.spinner("Generating 3 new hooks..."):
        try:
            updated_inp = deliverable.input_data.model_copy(deep=True)
            updated_inp.mode = "regenerate_hook"
            st.session_state.deliverable = pipeline.run(updated_inp, previous_deliverable=deliverable)
            st.toast("✅ Hooks regenerated successfully!", icon="🎣")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to regenerate hooks: {str(e)}")

# CTA Regeneration
if st.button("🎯 Regenerate CTA Options", use_container_width=True):
    with st.spinner("Regenerating CTA matching objective..."):
        try:
            updated_inp = deliverable.input_data.model_copy(deep=True)
            if new_cta_obj.strip():
                updated_inp.objective = new_cta_obj.strip()
            updated_inp.mode = "regenerate_cta"
            st.session_state.deliverable = pipeline.run(updated_inp, previous_deliverable=deliverable)
            st.toast("✅ CTA options regenerated successfully!", icon="🎯")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to regenerate CTA: {str(e)}")
```

---

## 8. Offline Test Mocking for Search Tool & LLM

### Root Cause
`tests/test_pipeline.py:140` executes the full pipeline against live DuckDuckGo searches and network endpoints, causing tests to fail if offline or IP rate-limited.

### Code Changes

#### `tests/test_pipeline.py`
```python
from unittest.mock import patch, MagicMock

@patch("src.search_tool.search_web")
def test_fastapi_generate_endpoint_mocked(mock_search):
    """Verify script generation via FastAPI endpoint using deterministic mocks."""
    mock_search.return_value = [
        {"title": "Test Title", "url": "https://example.com/facts", "snippet": "Sample fact"}
    ]
    from fastapi.testclient import TestClient
    from api import app

    client = TestClient(app)
    payload = {
        "topic": "Why are businesses not getting leads from their websites?",
        "duration": 30,
        "tone": "Tanglish",
        "objective": "Get agency leads",
    }
    response = client.post("/api/v1/scripts/generate", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["deliverable"]["script"]["word_count"] > 0
```

---

## 9. Computed Word Count Property

### Root Cause
`word_count` was stored as a static integer field that had to be manually recomputed every time any segment of `ScriptDraft` was modified, risking state desynchronization.

### Code Changes

#### `src/models.py`
Use Pydantic's `@computed_field` to guarantee `word_count` is always reactive and accurate:
```python
from pydantic import BaseModel, Field, computed_field

class ScriptDraft(BaseModel):
    hooks: List[HookItem] = Field(default_factory=list)
    hook: str = ""
    context: str = ""
    body_points: List[str] = Field(default_factory=list)
    engagement: str = ""
    cta: str = ""
    cta_options: List[CtaOptionItem] = Field(default_factory=list)
    on_screen_texts: List[str] = Field(default_factory=list)
    caption: str = ""
    hashtags: List[str] = Field(default_factory=list)
    estimated_duration: str = ""

    @computed_field
    @property
    def word_count(self) -> int:
        """Pure spoken words across all script segments, excluding bullet numbering."""
        cleaned_points = [re.sub(r"^\d+[\.\)]\s*", "", p) for p in self.body_points]
        raw_text = f"{self.hook} {self.context} {' '.join(cleaned_points)} {self.engagement} {self.cta}"
        tokens = re.findall(r"\b[\w\-']+\b", raw_text, flags=re.UNICODE)
        return len(tokens)
```

---

## 10. Streamlit Frontend Optimization for Arbitrary Topics

### Objectives
1. Clearly decouple the **3 assignment test samples** from custom topic entry.
2. Provide a prominent custom topic input with an empty default, guided suggestions, and clean reset capabilities.
3. Allow users to test arbitrary topics (finance, career, AI, local retail, health, fitness, travel) effortlessly.

### Code Changes

#### `app.py` (Sidebar Redesign)
```python
# --- SIDEBAR: TOPIC SELECTION & PARAMETERS ---
with st.sidebar:
    st.header("⚙️ Script Generator")

    mode_choice = st.radio(
        "Topic Source",
        options=["✍️ Custom Topic (Any Niche)", "🧪 Test Assignment Presets (3 Samples)"],
        index=0,
        help="Choose between testing your own topic or loading one of the 3 assignment benchmarks.",
    )

    if mode_choice == "🧪 Test Assignment Presets (3 Samples)":
        chosen_preset = st.selectbox("Select Test Sample", options=list(PRESETS.keys())[1:], index=0)
        preset_data = PRESETS[chosen_preset]
        default_topic = preset_data["topic"]
        default_duration = preset_data["duration"]
        default_tone = preset_data["tone"]
        default_objective = preset_data["objective"]
        default_audience = preset_data["audience"]
        default_niche = preset_data["niche"]
    else:
        chosen_preset = None
        default_topic = ""
        default_duration = 30
        default_tone = "Tanglish"
        default_objective = "awareness"
        default_audience = "General Tamil audience"
        default_niche = "Digital / Business"

    topic = st.text_area(
        "Primary Video Topic *",
        value=default_topic,
        placeholder="Enter ANY topic (e.g., 'How to start SIP investment in Tamil', 'Best AI tools for students 2025', 'EV scooter maintenance tips')...",
        height=100,
    )

    platform = st.selectbox(
        "Target Platform",
        options=["Instagram Reels", "YouTube Shorts", "Facebook Reels"],
        index=0,
    )

    duration = st.select_slider(
        "Target Duration (seconds)",
        options=[30, 45, 60],
        value=default_duration,
        help="Calibrated to natural spoken Tamil/Tanglish pacing (~2.2 words/second).",
    )

    limits = WORD_COUNT_LIMITS.get(duration, {"min": 60, "max": 75})
    st.caption(f"⏱️ Spoken target window: **{limits['min']} – {limits['max']} words**")

    tone_options = ["Tanglish", "conversational spoken Tamil", "Tamil"]
    tone_index = tone_options.index(default_tone) if default_tone in tone_options else 0
    tone = st.radio(
        "Script Language & Tone",
        options=tone_options,
        index=tone_index,
        help="Tanglish: Spoken Tamil written in English letters. Conversational Tamil: Natural spoken Tamil script.",
    )

    objective = st.text_input(
        "Marketing Objective",
        value=default_objective,
        placeholder="e.g., Get agency leads, drive WhatsApp DMs, profile visits",
    )

    with st.expander("Target Persona & Niche (Optional)"):
        audience = st.text_input("Target Audience", value=default_audience)
        niche = st.text_input("Niche / Category", value=default_niche)

    generate_btn = st.button("🚀 Generate Reel Script", type="primary", use_container_width=True)
```

---

## Summary of Files to Modify

| File | Changes Made |
| :--- | :--- |
| `src/config.py` | Fix Gemini model default (`gemini-1.5-flash`). |
| `src/llm.py` | Robust code-block JSON parser; remove non-greedy brace limitation; fix Gemini model fallback. |
| `src/models.py` | Add Pydantic field bounds; convert `word_count` to `@computed_field`; add `CtaOptionItem` & `cta_options`. |
| `src/agents/quality_agent.py` | Synchronize revised hook with `draft.hooks` recommended item. |
| `src/agents/script_agent.py` | Retain all 3 regenerated CTA options in `ScriptDraft`. |
| `main.py` | Implement full CLI with `--topic`, `--from-deliverable`, and `--server` options. |
| `api.py` | Correct CORS configuration (`allow_credentials=False` with wildcard origins). |
| `app.py` | Add custom topic vs preset selector; wrap hook/CTA regeneration buttons in `try...except`. |
| `tests/test_pipeline.py` | Add unit tests with mocked DuckDuckGo search and offline safety. |
