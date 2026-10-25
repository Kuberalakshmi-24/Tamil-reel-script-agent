"""CLI entrypoint for running the Tamil Reel Script Agent."""

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

import argparse
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from src.models import ScriptInput
from src.pipeline import TamilReelScriptPipeline

console = Console(safe_box=True)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tamil Reel Script Agent for VG Digital Falcon — Research-backed short-form video scripts."
    )
    parser.add_argument(
        "--topic",
        "-t",
        required=True,
        help="The primary video topic (e.g. 'Why are businesses not getting leads from their websites?')",
    )
    parser.add_argument(
        "--audience",
        "-a",
        default=None,
        help="Target audience (e.g. 'Small business owners')",
    )
    parser.add_argument(
        "--niche",
        default=None,
        help="Niche / industry domain",
    )
    parser.add_argument(
        "--platform",
        "-p",
        choices=["Instagram Reels", "YouTube Shorts", "Facebook Reels"],
        default=None,
        help="Target short-form platform (default: Instagram Reels)",
    )
    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        choices=[30, 45, 60],
        default=None,
        help="Script duration in seconds (30, 45, or 60; default: 30)",
    )
    parser.add_argument(
        "--tone",
        choices=["Tamil", "Tanglish", "conversational spoken Tamil"],
        default=None,
        help="Tone / script format: 'Tamil' (Tamil script) or 'Tanglish' (English alphabet)",
    )
    parser.add_argument(
        "--objective",
        "-o",
        default=None,
        help="Marketing objective (e.g. 'Get agency leads', 'awareness')",
    )
    parser.add_argument(
        "--mode",
        "-m",
        choices=["full_script", "regenerate_hook", "regenerate_cta"],
        default="full_script",
        help="Operation mode (default: full_script)",
    )
    parser.add_argument(
        "--output",
        help="Optional path to save generated markdown file",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print(f">> Starting Tamil Reel Script Agent for: {args.topic}\n")

    inp = ScriptInput.create_with_defaults(
        topic=args.topic,
        audience=args.audience,
        niche=args.niche,
        platform=args.platform,
        duration=args.duration,
        tone=args.tone,
        objective=args.objective,
        mode=args.mode,
    )

    pipeline = TamilReelScriptPipeline()
    deliverable = pipeline.run(inp)

    md_content = deliverable.to_markdown()

    # Pretty print in console
    try:
        console.print(Markdown(md_content))
    except Exception:
        print(md_content)

    # Save to file if specified
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md_content, encoding="utf-8")
        print(f"\n[SAVED] Deliverable saved to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
