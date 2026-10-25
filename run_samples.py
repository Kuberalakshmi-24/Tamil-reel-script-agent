"""Batch runner to generate the 3 mandatory sample deliverables specified in the assignment."""

import sys
import io

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from pathlib import Path
from rich.console import Console
from src.models import ScriptInput
from src.pipeline import TamilReelScriptPipeline
from src.config import DELIVERABLES_DIR

console = Console(safe_box=True)

TEST_CASES = [
    {
        "filename": "topic1_website_leads.md",
        "input": ScriptInput.create_with_defaults(
            topic="Why are businesses not getting leads from their websites?",
            audience="Small business owners",
            platform="Instagram Reels",
            duration=30,
            tone="Tanglish",
            objective="Get agency leads",
        ),
    },
    {
        "filename": "topic2_seo_mistakes.md",
        "input": ScriptInput.create_with_defaults(
            topic="Common SEO mistakes and ranking myths for small businesses",
            audience="Local shop owners and Tamil entrepreneurs",
            platform="Instagram Reels",
            duration=45,
            tone="Tanglish",
            objective="awareness",
        ),
    },
    {
        "filename": "topic3_germany_visa.md",
        "input": ScriptInput.create_with_defaults(
            topic="Germany Opportunity Card (Chancenkarte) and job seeker visa requirements",
            audience="Tamil graduates and tech professionals planning to work in Germany",
            platform="Instagram Reels",
            duration=60,
            tone="conversational spoken Tamil",
            objective="awareness",
        ),
    },
]


def run_all_samples():
    print(">> Running Tamil Reel Script Agent for 3 Sample Test Topics...\n")
    pipeline = TamilReelScriptPipeline()

    for i, test in enumerate(TEST_CASES, 1):
        inp = test["input"]
        filename = test["filename"]
        out_path = DELIVERABLES_DIR / filename

        print(f"({i}/{len(TEST_CASES)}) Processing Topic: {inp.topic}")
        print(f"  Duration: {inp.duration}s | Tone: {inp.tone} | Objective: {inp.objective}")

        deliverable = pipeline.run(inp)
        md_text = deliverable.to_markdown()

        out_path.write_text(md_text, encoding="utf-8")
        print(f"  [SAVED] {out_path}\n")

    print(">> All 3 sample deliverables generated successfully in deliverables/ directory!")


if __name__ == "__main__":
    run_all_samples()
