"""Master Pipeline orchestrating the 3-step script generation process."""

import logging
from typing import Optional
from src.models import (
    ScriptInput,
    ResearchResult,
    ScriptDraft,
    QualityCheckResult,
    FullDeliverable,
)
from src.llm import LLMClient
from src.agents.research_agent import ResearchAgent
from src.agents.script_agent import ScriptAgent
from src.agents.quality_agent import QualityAgent

logger = logging.getLogger(__name__)


class TamilReelScriptPipeline:
    """Orchestrates Research -> Scriptwriting -> Quality Check & Self-Correction."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.research_agent = ResearchAgent(self.llm)
        self.script_agent = ScriptAgent(self.llm)
        self.quality_agent = QualityAgent(self.llm)

    def run(self, inp: ScriptInput, previous_deliverable: Optional[FullDeliverable] = None) -> FullDeliverable:
        """Execute generation pipeline based on mode."""
        logger.info(f"Running pipeline for topic: '{inp.topic}' | Mode: '{inp.mode}'")

        if inp.mode == "regenerate_hook":
            if not previous_deliverable:
                # If no prior deliverable, generate full first
                inp.mode = "full_script"
                base = self._run_full(inp)
                inp.mode = "regenerate_hook"
                return self._regenerate_hook(inp, base)
            return self._regenerate_hook(inp, previous_deliverable)

        elif inp.mode == "regenerate_cta":
            if not previous_deliverable:
                inp.mode = "full_script"
                base = self._run_full(inp)
                inp.mode = "regenerate_cta"
                return self._regenerate_cta(inp, base)
            return self._regenerate_cta(inp, previous_deliverable)

        else:
            return self._run_full(inp)

    def _run_full(self, inp: ScriptInput) -> FullDeliverable:
        """Standard 3-Step Execution: Research -> Script -> Quality Check."""
        # Step 1: Research and Angle Selection
        logger.info("[Step 1/3] Executing Research Agent with web search...")
        research = self.research_agent.execute(inp)

        # Step 2: Scriptwriting & Hooks
        logger.info("[Step 2/3] Executing Script Agent for hooks and script...")
        draft = self.script_agent.execute(inp, research)

        # Step 3: Quality Check & Self-Correction
        logger.info("[Step 3/3] Executing Quality Compliance Agent...")
        qc = self.quality_agent.execute(inp, research, draft)

        return FullDeliverable(
            input_data=inp,
            research=research,
            script=draft,
            quality_check=qc,
        )

    def _regenerate_hook(self, inp: ScriptInput, base: FullDeliverable) -> FullDeliverable:
        """Regenerate only hooks while reusing existing research and script body."""
        logger.info("Executing targeted regeneration for HOOKS...")
        updated_draft = self.script_agent.regenerate_hooks(inp, base.script)
        qc = self.quality_agent.execute(inp, base.research, updated_draft)

        return FullDeliverable(
            input_data=inp,
            research=base.research,
            script=updated_draft,
            quality_check=qc,
        )

    def _regenerate_cta(self, inp: ScriptInput, base: FullDeliverable) -> FullDeliverable:
        """Regenerate only CTA while reusing existing research and script body."""
        logger.info("Executing targeted regeneration for CTA...")
        updated_draft = self.script_agent.regenerate_cta(inp, base.script)
        qc = self.quality_agent.execute(inp, base.research, updated_draft)

        return FullDeliverable(
            input_data=inp,
            research=base.research,
            script=updated_draft,
            quality_check=qc,
        )
