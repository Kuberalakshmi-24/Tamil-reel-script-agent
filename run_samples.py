"""Batch runner to generate the 3 mandatory sample deliverables specified in the assignment."""

from src.utils import setup_utf8_console

setup_utf8_console()

from pathlib import Path
from src.models import ScriptInput
from src.pipeline import TamilReelScriptPipeline
from src.config import DELIVERABLES_DIR

TEST_CASES = [
    {
        "stem": "topic1_website_leads",
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
        "stem": "topic2_seo_mistakes",
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
        "stem": "topic3_germany_visa",
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
        stem = test["stem"]
        out_base = DELIVERABLES_DIR / stem

        print(f"({i}/{len(TEST_CASES)}) Processing Topic: {inp.topic}")
        print(f"  Duration: {inp.duration}s | Tone: {inp.tone} | Objective: {inp.objective}")

        deliverable = pipeline.run(inp)
        deliverable.save_deliverables(out_base)

        print(f"  [SAVED] {out_base.with_suffix('.md')}")
        print(f"  [SAVED] {out_base.with_suffix('.json')}\n")

    print(">> All 3 sample deliverables generated successfully in deliverables/ directory!")


if __name__ == "__main__":
    run_all_samples()
