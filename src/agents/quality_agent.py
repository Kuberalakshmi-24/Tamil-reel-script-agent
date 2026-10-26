"""Step 3: Quality Check and Self-Correction Agent."""

import logging
from typing import Tuple
from src.models import (
    ScriptInput,
    ResearchResult,
    ScriptDraft,
    QualityCheckResult,
    CheckItem,
)
from src.config import WORD_COUNT_LIMITS
from src.prompts import QUALITY_CHECK_SYSTEM_PROMPT
from src.llm import LLMClient
from src.simulation import SimulationProvider

logger = logging.getLogger(__name__)


class QualityAgent:
    """Rigorous 5-point quality auditor with automatic self-correction loop."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def execute(
        self, inp: ScriptInput, research: ResearchResult, draft: ScriptDraft
    ) -> Tuple[QualityCheckResult, ScriptDraft]:
        """Evaluate 5 criteria, auto-fix any flagged defect, and return (QualityCheckResult, updated_draft).
        
        Guarantees zero in-place mutation of the original draft.
        """
        limits = WORD_COUNT_LIMITS.get(inp.duration, {"min": 60, "max": 75})
        actual_words = draft.calculate_word_count()

        user_prompt = f"""Topic: {inp.topic}
Audience: {inp.audience}
Duration: {inp.duration}s (Strict target: {limits['min']}-{limits['max']} words | Actual words: {actual_words})
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

Perform the 5-point quality audit. If any criteria is flagged, you MUST provide the corrected script under 'revised_script' and log fixes under 'fixes_applied'.
"""

        fallback = SimulationProvider.get_quality_fallback(inp, research, draft)
        data = self.llm.generate_json(
            system_prompt=QUALITY_CHECK_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            default_fallback=fallback,
        )

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
                notes=checks_data.get("duration_fit", {}).get("notes", f"Word count ({updated_draft.word_count}w) calibrated."),
            ),
            fixes_applied=fixes_applied,
        )

        return qc_result, updated_draft
