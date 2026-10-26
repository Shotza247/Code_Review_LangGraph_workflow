from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


def load_settings(path: str | Path | None = None, overrides: dict | None = None) -> dict:
    """Load settings.yaml, then apply dotted-key overrides, e.g. {"llm.provider": "openai"}."""
    load_dotenv(ROOT / ".env")
    path = Path(path) if path else ROOT / "config" / "settings.yaml"
    settings = yaml.safe_load(path.read_text(encoding="utf-8"))
    for dotted, value in (overrides or {}).items():
        if value is None:
            continue
        cur = settings
        *parents, last = dotted.split(".")
        for p in parents:
            cur = cur.setdefault(p, {})
        cur[last] = value
    return settings


def load_rubric(name: str = "reproducibility") -> dict:
    return yaml.safe_load((ROOT / "rubrics" / f"{name}.yaml").read_text(encoding="utf-8"))


def pr_mode(settings: dict) -> str:
    mode = settings.get("pr", {}).get("mode", "off")
    return "off" if mode in (False, None) else str(mode).lower()
