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

    # Launch server if requested or if run without CLI arguments
    if args.server or (not args.topic and not args.from_deliverable and len(sys.argv) == 1):
        import uvicorn
        print(f">> Starting Tamil Reel Script Agent API Backend on http://localhost:{args.port}")
        print(f">> Interactive Swagger Documentation: http://localhost:{args.port}/docs")
        print(f">> ReDoc Schema: http://localhost:{args.port}/redoc\n")
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
