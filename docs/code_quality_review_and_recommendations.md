# Tamil Reel Script Agent — Code Quality Review & Recommendations

**Repository:** `Tamil-reel-script-agent`  
**Purpose:** Automated 3-step AI pipeline for research-backed Tamil & Tanglish short-form video scripts (Instagram Reels, YouTube Shorts, Facebook Reels).  
**Review Focus:** Clean, simple, robust architecture tailored specifically to this task.

---

## 1. Executive Summary & Quality Scorecard

The project implements a solid 3-step architectural separation of concerns (**Step 1: Research** ➔ **Step 2: Scriptwriting** ➔ **Step 3: Quality Audit**), adhering strictly to the required 6-section deliverable schema and spoken pacing calibration (~2.2 words/second).

However, to make the codebase truly **clean, simple, and production-grade**, several critical issues—specifically hardcoded mock scripts, broken regeneration state management, hallucinated search URLs, and in-place mutations—must be refactored.

| Dimension | Grade | Assessment |
| :--- | :---: | :--- |
| **Architecture & Separation of Concerns** | **B+** | Good modular split between research, scriptwriting, and quality auditing steps. |
| **Code Simplicity & Cleanliness** | **C** | Bloated with **200+ lines** of static, copy-pasted Tamil scripts inside live agent classes. |
| **State Management & Regeneration** | **D** | Regeneration mode (`regenerate_hook` / `regenerate_cta`) lacks persistence in the CLI, causing duplicate execution. |
| **Anti-Hallucination & Integrity** | **C+** | Search tool injects a fabricated URL (`https://official.info/verify`), violating core safety rules. |
| **Speech Calibration (Pacing)** | **B-** | Naive whitespace `.split()` counts punctuation and bullet numbers (`"1."`) as spoken words. |
| **Production Readiness** | **B-** | Missing Gemini integration despite config definitions; no unit tests; broken absolute paths in `README.md`. |

---

## 2. Key Strengths of the Current Codebase

1. **Strict 6-Section Output Compliance:**  
   `src/models.py:to_markdown()` deterministically formats deliverables into the required 6 sections + Quality Check block.
2. **Pydantic Data Contracts:**  
   Strong typing across all pipeline stages (`ScriptInput`, `ResearchResult`, `ScriptDraft`, `QualityCheckResult`, `FullDeliverable`).
3. **Calibrated Spoken Duration:**  
   Pacing is accurately bounded to ~2.2 words per second for spoken Tamil:
   * **30s:** 60 – 75 words
   * **45s:** 95 – 110 words
   * **60s:** 125 – 145 words
4. **Enhanced Terminal DX:**  
   Clean CLI output formatting using `rich.console` and Markdown rendering.

---

## 3. Core Issues & Recommendations (Prioritized)

### 3.1. Strip Hardcoded Simulation Bloat from Core Agents
* **Files:** [`src/agents/script_agent.py`](file:///c:/Users/kumar/Desktop/Tamil-reel-script-agent/src/agents/script_agent.py#L52-L175) and [`src/agents/research_agent.py`](file:///c:/Users/kumar/Desktop/Tamil-reel-script-agent/src/agents/research_agent.py#L58-L126)
* **The Issue:**  
  `script_agent.py` contains ~120 lines of hardcoded Tamil/Tanglish copy under `create_simulation_fallback()`, with rigid branches:
  ```python
  if "lead" in topic_lower or "website" in topic_lower: ...
  elif "seo" in topic_lower: ...
  else: # Germany / Visa / General
  ```
  If an unlisted topic is provided without an API key (e.g. `python main.py --topic "Real estate in Chennai"`), it falls into the `else` branch and generates a script about **Germany Chancenkarte**!
* **Recommendation:**  
  Remove the hardcoded fallback scripts from production agent classes. Agents should strictly focus on prompt composition, LLM calling, and response validation. If an offline mock is required, place it in an explicit `tests/mocks/` provider or fail cleanly with an informative configuration message. This reduces `script_agent.py` from **281 lines down to ~65 lines**.

---

### 3.2. Fix Broken Regeneration Mode & State Loss
* **Files:** [`src/pipeline.py`](file:///c:/Users/kumar/Desktop/Tamil-reel-script-agent/src/pipeline.py#L33-L49), [`main.py`](file:///c:/Users/kumar/Desktop/Tamil-reel-script-agent/main.py#L87-L121)
* **The Issue:**  
  The assignment specification mandates:
  > *"Never rewrite the full script in these modes. Reuse the previous research; do not search again unless asked."*

  Currently, `main.py` has no mechanism to pass a prior deliverable. Running:
  ```bash
  python main.py --topic "Why websites fail" --mode regenerate_hook
  ```
  causes `pipeline.py` to run `_run_full()` (live search + full scriptwriting + QC) and **then** immediately run `_regenerate_hook()` and QC a second time. This doubles execution time and API costs.
* **Recommendation:**  
  1. Add `.save_deliverables()` and `.load_from_json()` to `FullDeliverable` to persist state as both `.md` and `.json`.
  2. Add `--from-deliverable <path.json>` to `main.py` to allow instant hook/CTA regeneration from disk without repeating web searches.

---

### 3.3. Eliminate Fake URLs from Search Tool (Zero-Hallucination Mandate)
* **File:** [`src/search_tool.py`](file:///c:/Users/kumar/Desktop/Tamil-reel-script-agent/src/search_tool.py#L38-L43)
* **The Issue:**  
  When DuckDuckGo fails or encounters network errors, the code injects:
  ```python
  results.append({
      "title": f"Search fallback for: {query}",
      "url": "https://official.info/verify",
      "snippet": f"Official documentation and industry standard data regarding {query}.",
  })
  ```
  Inventing a fake domain (`https://official.info/verify`) and presenting it as verified research directly violates the anti-hallucination mandate:
  > *"NEVER invent statistics, links... If no source supports it, mark it 'UNVERIFIED' or drop it."*
* **Recommendation:**  
  If the search fails or returns zero results, return an empty list `[]`. Let `ResearchAgent` transparently mark findings as unverified or report that live search was unavailable.

---

### 3.4. Avoid In-Place State Mutation in `QualityAgent`
* **File:** [`src/agents/quality_agent.py`](file:///c:/Users/kumar/Desktop/Tamil-reel-script-agent/src/agents/quality_agent.py#L131-L144)
* **The Issue:**  
  `QualityAgent.execute(inp, research, draft)` directly mutates `draft` in place (`draft.hook = revised["hook"]`, etc.) while also returning `QualityCheckResult`. In-place mutation creates unpredictable side effects and complicates testing.
* **Recommendation:**  
  Return a clean tuple:
  ```python
  return qc_result, updated_draft
  ```
  Or return a fresh copy using Pydantic: `updated_draft = draft.model_copy(deep=True)`.

---

### 3.5. Fix Naive Spoken Word-Count Tokenization
* **File:** [`src/models.py`](file:///c:/Users/kumar/Desktop/Tamil-reel-script-agent/src/models.py#L124-L128)
* **The Issue:**  
  `calculate_word_count()` splits text with `len(raw_text.split())`:
  1. Bullet numbers (e.g., `"1. Hero section..."`) are counted as spoken words.
  2. Punctuation marks attached to words skew word tokens.
  3. Tamil Unicode text word splitting should strip symbols.
* **Recommendation:**  
  Strip bullet numbering and count spoken words accurately using Unicode-aware regex:
  ```python
  import re

  def calculate_word_count(self) -> int:
      cleaned_points = [re.sub(r"^\d+[\.\)]\s*", "", p) for p in self.body_points]
      spoken = f"{self.hook} {self.context} {' '.join(cleaned_points)} {self.engagement} {self.cta}"
      words = re.findall(r"\b[\w\-']+\b", spoken, flags=re.UNICODE)
      return len(words)
  ```

---

### 3.6. Robust Non-Greedy JSON Parsing & Google Gemini Support
* **Files:** [`src/config.py`](file:///c:/Users/kumar/Desktop/Tamil-reel-script-agent/src/config.py#L29), [`src/llm.py`](file:///c:/Users/kumar/Desktop/Tamil-reel-script-agent/src/llm.py#L18-L40)
* **The Issue:**  
  1. `clean_json_response()` uses greedy regex: `re.search(r"\{.*\}", text, re.DOTALL)`. If the LLM returns commentary containing curly braces before or after the code block, parsing fails.
  2. `GEMINI_API_KEY` is loaded in `config.py`, but `llm.py` completely lacks Gemini handling.
* **Recommendation:**  
  Use non-greedy fence extraction:
  ```python
  match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
  ```
  Add native Google Gemini support (`gemini-1.5-flash`), which is free, highly capable in Indian languages, and natively produces conversational Tamil and Tanglish.

---

### 3.7. Code Hygiene & Documentation Cleanliness
* **Duplicated Windows UTF-8 Boilerplate:** Both [`main.py`](file:///c:/Users/kumar/Desktop/Tamil-reel-script-agent/main.py#L6-L13) and [`run_samples.py`](file:///c:/Users/kumar/Desktop/Tamil-reel-script-agent/run_samples.py#L6-L13) repeat the identical 14-line Windows stdout/stderr reconfiguration block. Move this to a shared utility function.
* **Broken Hardcoded Link in README:** [`README.md:L133-L135`](file:///c:/Users/kumar/Desktop/Tamil-reel-script-agent/README.md#L132-L135) links to `file:///c:/Users/kuber/...` (pointing to a foreign local drive). Convert these to clean relative paths (`deliverables/topic1_website_leads.md`).

---

## 4. File-by-File Quality Audit Table

| File | Current Lines | Code Smells & Architectural Issues | Clean & Simple Remedy |
| :--- | :---: | :--- | :--- |
| **`src/agents/script_agent.py`** | 281 | ~120 lines of hardcoded Tamil script fallbacks; rigid branching. | Remove fallback scripts; reduce to ~65 lines focused purely on prompting and parsing. |
| **`src/agents/research_agent.py`** | 156 | Hardcoded fallback search snippets; regex query generator only handles English queries. | Return empty/honest citations if search fails; extract search terms cleanly. |
| **`src/agents/quality_agent.py`** | 168 | In-place mutation of `draft`; fallback appends arbitrary generic sentences. | Return `(QualityCheckResult, ScriptDraft)`; avoid in-place side effects. |
| **`src/pipeline.py`** | 99 | Discards previous deliverable state when run from CLI; duplicates execution. | Accept and pass `previous_deliverable` state from disk. |
| **`src/search_tool.py`** | 61 | Fabricates fake URL `https://official.info/verify` on error. | Return `[]` on error to guarantee zero hallucinated links. |
| **`src/llm.py`** | 113 | Greedy regex for JSON; `GEMINI_API_KEY` defined in config but unsupported in code. | Use non-greedy regex; add Gemini / Groq support. |
| **`src/models.py`** | 243 | Word count counts numbering bullets; lacks JSON load/save methods. | Refine regex token counting; add `.save()` and `.load()` helpers. |
| **`main.py`** | 124 | Missing CLI flag to load prior deliverable for hook/CTA regeneration; duplicated UTF-8 block. | Add `--from-deliverable`; extract UTF-8 boilerplate. |
| **`README.md`** | 136 | Broken hardcoded link `file:///c:/Users/kuber/...`. | Convert links to relative paths (`deliverables/...`). |

---

## 5. Clean & Simple Refactoring Blueprint

### Refactored `ScriptAgent.execute()` Example
```python
class ScriptAgent:
    """Generates 3 hook options, timed spoken script, and production notes."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def execute(self, inp: ScriptInput, research: ResearchResult) -> ScriptDraft:
        limits = WORD_COUNT_LIMITS.get(inp.duration, {"min": 60, "max": 75, "target": 68})
        
        user_prompt = f"""Topic: {inp.topic}
Audience: {inp.audience} | Platform: {inp.platform} | Duration: {inp.duration}s ({limits['min']}-{limits['max']} words)
Tone: {inp.tone} | Objective: {inp.objective}

RESEARCH FINDINGS:
{chr(10).join(f"- {f}" for f in research.key_findings)}

CHOSEN CONTENT ANGLE:
{research.chosen_angle} (Reason: {research.angle_reason})

PAIN POINTS:
{chr(10).join(f"- {p}" for p in research.pain_points)}
"""
        # Clean, direct LLM execution without embedded mock copy
        data = self.llm.generate_json(system_prompt=SCRIPT_SYSTEM_PROMPT, user_prompt=user_prompt)
        
        draft = ScriptDraft.model_validate(data)
        draft.word_count = draft.calculate_word_count()
        return draft
```

---

## 6. Actionable Implementation Checklist

- [ ] **1. Decouple Mocks:** Delete the ~200 lines of hardcoded simulation functions inside `script_agent.py` and `research_agent.py`.
- [ ] **2. Harden Search Tool:** Update `search_tool.py` to return `[]` on failure instead of the fabricated `https://official.info/verify` URL.
- [ ] **3. Implement State Persistence:** Add `.save_deliverables()` and `.load_from_json()` to `FullDeliverable`, and support `--from-deliverable` in `main.py`.
- [ ] **4. Prevent In-Place Mutation:** Refactor `QualityAgent.execute()` to return `Tuple[QualityCheckResult, ScriptDraft]`.
- [ ] **5. Refine Word Counting:** Use Unicode-aware regex in `calculate_word_count()` to ignore bullet numbering and punctuation.
- [ ] **6. Add Gemini Integration:** Support `gemini` in `llm.py` via `google-genai` or standard SDK for high-quality, free-tier Tamil and Tanglish generation.
- [ ] **7. Clean Documentation:** Replace hardcoded `file:///c:/Users/kuber/...` paths in `README.md` with repository-relative paths.
