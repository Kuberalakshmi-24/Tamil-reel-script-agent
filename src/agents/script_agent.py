"""Step 2: Scriptwriter Agent for Hooks, Scriptwriting, and Production Notes."""

import logging
from src.models import (
    ScriptInput,
    ResearchResult,
    ScriptDraft,
    HookItem,
    CtaOptionItem,
)
from src.config import WORD_COUNT_LIMITS
from src.prompts import (
    SCRIPT_SYSTEM_PROMPT,
    REGENERATE_HOOK_PROMPT,
    REGENERATE_CTA_PROMPT,
)
from src.llm import LLMClient
from src.simulation import SimulationProvider

logger = logging.getLogger(__name__)


class ScriptAgent:
    """Generates 3 hook options, timed spoken script, and production notes."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def execute(self, inp: ScriptInput, research: ResearchResult) -> ScriptDraft:
        """Generate full script draft matching duration and tone guidelines."""
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

        fallback = SimulationProvider.get_script_fallback(inp, research)
        data = self.llm.generate_json(
            system_prompt=SCRIPT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            default_fallback=fallback,
        )

        hooks_list = [
            HookItem(
                text=h.get("text", ""),
                type=h.get("type", "bold statement"),
                is_recommended=h.get("is_recommended", False),
                reason=h.get("reason", ""),
            )
            for h in data.get("hooks", [])
        ]

        # Ensure at least one hook is recommended
        if hooks_list and not any(h.is_recommended for h in hooks_list):
            hooks_list[0].is_recommended = True
            hooks_list[0].reason = "Selected as most compelling angle."

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
        return draft

    def regenerate_hooks(self, inp: ScriptInput, draft: ScriptDraft) -> ScriptDraft:
        """Regenerate only hook options and swap recommended hook."""
        prompt = f"""Topic: {inp.topic}
Tone: {inp.tone}
Current Script Body:
{chr(10).join(draft.body_points)}

Generate 3 brand new punchy hooks (question, bold statement, pain-point), max 12 words each."""

        fallback = SimulationProvider.get_hooks_fallback(inp, draft)
        data = self.llm.generate_json(
            system_prompt=REGENERATE_HOOK_PROMPT,
            user_prompt=prompt,
            default_fallback=fallback,
        )

        new_hooks = [
            HookItem(
                text=h.get("text", ""),
                type=h.get("type", "bold statement"),
                is_recommended=h.get("is_recommended", False),
                reason=h.get("reason", ""),
            )
            for h in data.get("hooks", [])
        ]
        rec_text = data.get("recommended_hook", new_hooks[0].text if new_hooks else draft.hook)

        updated_draft = draft.model_copy(deep=True)
        updated_draft.hooks = new_hooks
        updated_draft.hook = rec_text
        return updated_draft

    def regenerate_cta(self, inp: ScriptInput, draft: ScriptDraft) -> ScriptDraft:
        """Regenerate only CTA options and swap in the best CTA."""
        prompt = f"""Topic: {inp.topic}
Objective: {inp.objective}
Tone: {inp.tone}

Generate 3 NEW specific, non-vague CTA options matching the objective."""

        fallback = SimulationProvider.get_cta_fallback(inp, draft)
        data = self.llm.generate_json(
            system_prompt=REGENERATE_CTA_PROMPT,
            user_prompt=prompt,
            default_fallback=fallback,
        )

        cta_options_raw = data.get("cta_options", [])
        cta_items = [
            CtaOptionItem(
                text=c.get("text", ""),
                is_recommended=c.get("is_recommended", False),
                reason=c.get("reason", ""),
            )
            for c in cta_options_raw
            if c.get("text")
        ]
        rec_cta = data.get("recommended_cta") or (cta_items[0].text if cta_items else draft.cta)

        updated_draft = draft.model_copy(deep=True)
        updated_draft.cta = rec_cta
        if cta_items:
            updated_draft.cta_options = cta_items
        return updated_draft
