#!/usr/bin/env python
"""Usage: python run.py https://github.com/owner/repo [--provider openai] [--pr fork]"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from readme_sync.config import load_settings  # noqa: E402
from readme_sync.graph import build_graph  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit and sync a GitHub repo's README.")
    ap.add_argument("repo_url")
    ap.add_argument("--config", help="path to settings.yaml")
    ap.add_argument("--provider", choices=["huggingface", "openai"])
    ap.add_argument("--model", help="override the model for the chosen provider")
    ap.add_argument("--pr", choices=["off", "fork", "direct"], help="override pr.mode")
    args = ap.parse_args()

    settings = load_settings(args.config, {"llm.provider": args.provider, "pr.mode": args.pr})
    if args.model:
        settings["llm"][settings["llm"]["provider"]]["model"] = args.model

    result = build_graph(settings).invoke({"repo_url": args.repo_url})

    print(f"\nRepo:            {result['owner']}/{result['repo']}")
    print(f"Rating (README): {result['readme_rating_v1']['score']}/100")
    print(f"Rating (+code):  {result['readme_rating_v2']['score']}/100")
    print(f"Outputs:         {result['output_dir']}")
    if result.get("pr_url"):
        print(f"Pull request:    {result['pr_url']}")
    for err in result.get("errors", []):
        print(f"Warning: {err}")


if __name__ == "__main__":
    main()
