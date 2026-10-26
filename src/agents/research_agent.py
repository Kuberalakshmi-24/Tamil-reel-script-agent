"""Step 1: Research and Angle Selection Agent."""

import logging
import re
from typing import List
from src.models import ScriptInput, ResearchResult, SourceItem
from src.search_tool import run_research_queries
from src.prompts import RESEARCH_SYSTEM_PROMPT
from src.llm import LLMClient
from src.simulation import SimulationProvider

logger = logging.getLogger(__name__)


class ResearchAgent:
    """Executes live web search, extracts verified claims with URLs, and selects content angle."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def _generate_search_queries(self, inp: ScriptInput) -> List[str]:
        """Generate 3-5 targeted search queries for reputable sources."""
        t = inp.topic.strip()
        # Clean leading question phrases to prevent dictionary definition results
        cleaned = re.sub(r"^(why are|why do|why is|how to|what is|why)\s+", "", t, flags=re.IGNORECASE).rstrip("?")
        return [
            f"{cleaned} statistics facts data",
            f"{cleaned} common mistakes reasons",
            f"{cleaned} guide best practices",
            f"{cleaned} case study industry benchmark",
        ]

    def execute(self, inp: ScriptInput) -> ResearchResult:
        """Run web searches, extract verified facts, and pick content angle."""
        queries = self._generate_search_queries(inp)
        raw_results = run_research_queries(queries, max_per_query=3)

        # Format search snippets for LLM context
        context_snippets = []
        for i, item in enumerate(raw_results[:12], 1):
            context_snippets.append(
                f"[{i}] Title: {item.get('title')}\nURL: {item.get('url')}\nSnippet: {item.get('snippet')}\n"
            )
        formatted_context = "\n".join(context_snippets)

        user_prompt = f"""Topic: {inp.topic}
Audience: {inp.audience}
Niche: {inp.niche}
Objective: {inp.objective}

LIVE SEARCH RESULTS:
{formatted_context}

Please analyze these search results and output the research summary JSON strictly following the system prompt rules.
"""

        fallback = SimulationProvider.get_research_fallback(inp, raw_results)
        data = self.llm.generate_json(
            system_prompt=RESEARCH_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            default_fallback=fallback,
        )

        source_items = [
            SourceItem(
                url=s.get("url", ""),
                title=s.get("title", ""),
                claim_supported=s.get("claim_supported", ""),
                is_verified=s.get("is_verified", True),
            )
            for s in data.get("sources", [])
            if s.get("url")
        ]

        return ResearchResult(
            topic=inp.topic,
            queries_run=queries,
            key_findings=data.get("key_findings", []),
            pain_points=data.get("pain_points", []),
            chosen_angle=data.get("chosen_angle", ""),
            angle_reason=data.get("angle_reason", ""),
            sources=source_items,
            uncertainties=data.get("uncertainties", []),
        )
