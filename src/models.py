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


class ScriptInput(BaseModel):
    """Input payload for generating or modifying a script."""
    topic: str
    audience: Optional[str] = None
    niche: Optional[str] = None
    platform: str = DEFAULT_PLATFORM
    duration: int = DEFAULT_DURATION
    tone: str = DEFAULT_TONE
    objective: str = DEFAULT_OBJECTIVE
    mode: Literal["full_script", "regenerate_hook", "regenerate_cta"] = DEFAULT_MODE
    assumed_defaults: List[str] = Field(default_factory=list)

    @classmethod
    def create_with_defaults(
        cls,
        topic: str,
        audience: Optional[str] = None,
        niche: Optional[str] = None,
        platform: Optional[str] = None,
        duration: Optional[int] = None,
        tone: Optional[str] = None,
        objective: Optional[str] = None,
        mode: Optional[str] = None,
    ) -> "ScriptInput":
        """Instantiate with standard fallback defaults and track assumptions."""
        assumed = []
        final_platform = platform or DEFAULT_PLATFORM
        if not platform:
            assumed.append(f"platform = {DEFAULT_PLATFORM}")

        final_duration = duration if duration in (30, 45, 60) else DEFAULT_DURATION
        if not duration:
            assumed.append(f"duration = {DEFAULT_DURATION}s")

        final_tone = tone or DEFAULT_TONE
        if not tone:
            assumed.append(f"tone = {DEFAULT_TONE}")

        final_objective = objective or DEFAULT_OBJECTIVE
        if not objective:
            assumed.append(f"objective = {DEFAULT_OBJECTIVE}")

        final_mode = mode or DEFAULT_MODE

        return cls(
            topic=topic,
            audience=audience or "General Tamil content audience",
            niche=niche or "Business / Digital / Career",
            platform=final_platform,
            duration=final_duration,
            tone=final_tone,
            objective=final_objective,
            mode=final_mode,
            assumed_defaults=assumed,
        )


class SourceItem(BaseModel):
    url: str
    title: str = ""
    claim_supported: str
    is_verified: bool = True


class ResearchResult(BaseModel):
    """Output from Step 1: Research and Angle Selection."""
    topic: str
    queries_run: List[str] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)  # 3-5 facts/mistakes
    pain_points: List[str] = Field(default_factory=list)   # 3 audience pain points
    chosen_angle: str = ""
    angle_reason: str = ""
    sources: List[SourceItem] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)


class HookItem(BaseModel):
    text: str
    type: Literal["question", "bold statement", "pain-point"]
    is_recommended: bool = False
    reason: str = ""


class ScriptDraft(BaseModel):
    """Output from Step 2: Hooks, Script segments, and Production Notes."""
    hooks: List[HookItem] = Field(default_factory=list)
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

    def get_full_script_text(self) -> str:
        """Combine labeled script parts into full spoken text."""
        parts = [
            f"[Hook] {self.hook}",
            f"[Context] {self.context}",
            "[Body]",
            "\n".join(f"- {p}" for p in self.body_points),
            f"[Engagement] {self.engagement}",
            f"[CTA] {self.cta}",
        ]
        return "\n".join(parts)

    def calculate_word_count(self) -> int:
        """Calculate pure spoken words across all script segments, excluding bullet numbers."""
        # Strip leading numbers like '1. ', '2. '
        cleaned_points = [re.sub(r"^\d+[\.\)]\s*", "", p) for p in self.body_points]
        raw_text = f"{self.hook} {self.context} {' '.join(cleaned_points)} {self.engagement} {self.cta}"
        # Extract unicode words (handles both Latin Tanglish and Tamil Unicode)
        tokens = re.findall(r"\b[\w\-']+\b", raw_text, flags=re.UNICODE)
        return len(tokens)


class CheckItem(BaseModel):
    status: Literal["PASS", "FLAG"]
    notes: str


class QualityCheckResult(BaseModel):
    """Output from Step 3: 5-Point Quality Check & Self-Correction."""
    unsupported_claims: CheckItem
    repetition: CheckItem
    weak_cta: CheckItem
    unnatural_tamil: CheckItem
    duration_fit: CheckItem
    fixes_applied: List[str] = Field(default_factory=list)


class FullDeliverable(BaseModel):
    """The complete deliverable combining all 6 standard sections + QC report."""
    input_data: ScriptInput
    research: ResearchResult
    script: ScriptDraft
    quality_check: QualityCheckResult

    def to_markdown(self) -> str:
        """Format the output strictly according to the 6 sections + QC result."""
        lines = []

        # Header
        lines.append(f"# Tamil Reel Script: {self.input_data.topic}\n")

        # Section 1: Topic & Audience
        lines.append("## 1. Topic & Audience")
        lines.append(f"- **Topic:** {self.input_data.topic}")
        lines.append(f"- **Audience:** {self.input_data.audience}")
        lines.append(f"- **Platform:** {self.input_data.platform}")
        lines.append(f"- **Duration:** {self.input_data.duration} seconds")
        lines.append(f"- **Tone:** {self.input_data.tone}")
        lines.append(f"- **Objective:** {self.input_data.objective}")
        if self.input_data.assumed_defaults:
            lines.append(f"- **Assumed Defaults:** {', '.join(self.input_data.assumed_defaults)}")
        lines.append("")

        # Section 2: Research Summary
        lines.append("## 2. Research Summary")
        lines.append("### Key Findings:")
        for finding in self.research.key_findings:
            lines.append(f"- {finding}")
        lines.append(f"\n- **Chosen Content Angle:** {self.research.chosen_angle}")
        lines.append(f"- **Why Chosen:** {self.research.angle_reason}\n")

        # Section 3: Hook Options
        lines.append("## 3. Hook Options")
        for i, hook in enumerate(self.script.hooks, 1):
            badge = " **[RECOMMENDED]**" if hook.is_recommended else ""
            lines.append(f"{i}. *({hook.type})* \"{hook.text}\"{badge}")
            if hook.reason:
                lines.append(f"   - *Reason:* {hook.reason}")
        lines.append("")

        # Section 4: Full Tamil Script
        limits = WORD_COUNT_LIMITS.get(self.input_data.duration, {"min": 60, "max": 75})
        lines.append("## 4. Full Tamil Script")
        lines.append(f"*(Target: {limits['min']}-{limits['max']} words | Actual: **{self.script.word_count} words**)*\n")
        lines.append(f"**[Hook]**\n{self.script.hook}\n")
        lines.append(f"**[Context]**\n{self.script.context}\n")
        lines.append("**[Body]**")
        for point in self.script.body_points:
            lines.append(f"{point}")
        lines.append("")
        lines.append(f"**[Engagement]**\n{self.script.engagement}\n")
        lines.append(f"**[CTA]**\n{self.script.cta}\n")

        # Section 5: Production Notes
        lines.append("## 5. Production Notes")
        lines.append("- **On-Screen Text Suggestions:**")
        for ost in self.script.on_screen_texts:
            lines.append(f"  - {ost}")
        lines.append(f"- **Estimated Duration:** {self.script.estimated_duration}")
        lines.append(f"- **Caption:**\n  > {self.script.caption}")
        lines.append(f"- **Hashtags:** {' '.join(self.script.hashtags)}\n")

        # Section 6: Sources
        lines.append("## 6. Sources")
        if self.research.sources:
            for s in self.research.sources:
                status = "" if s.is_verified else " *(UNVERIFIED)*"
                lines.append(f"- [{s.title or s.url}]({s.url}){status} — *Supports:* {s.claim_supported}")
        else:
            lines.append("- *No external sources logged.*")

        if self.research.uncertainties:
            lines.append("\n### Uncertainty / Verify on Official Site:")
            for u in self.research.uncertainties:
                lines.append(f"- ⚠️ {u}")
        lines.append("")

        # Quality Check Result
        lines.append("## Quality Check Result")
        qc = self.quality_check
        lines.append(f"1. **Unsupported Claims:** [{qc.unsupported_claims.status}] {qc.unsupported_claims.notes}")
        lines.append(f"2. **Repetition:** [{qc.repetition.status}] {qc.repetition.notes}")
        lines.append(f"3. **Weak CTA:** [{qc.weak_cta.status}] {qc.weak_cta.notes}")
        lines.append(f"4. **Unnatural Tamil:** [{qc.unnatural_tamil.status}] {qc.unnatural_tamil.notes}")
        lines.append(f"5. **Duration Fit:** [{qc.duration_fit.status}] {qc.duration_fit.notes}")

        if qc.fixes_applied:
            lines.append("\n**Auto-Corrections Applied:**")
            for fix in qc.fixes_applied:
                lines.append(f"- {fix}")
        else:
            lines.append("\n*All checks passed with zero revisions required.*")

        lines.append("")
        return "\n".join(lines)

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
        """Load deliverable state from JSON."""
        return cls.model_validate_json(json_path.read_text(encoding="utf-8"))

