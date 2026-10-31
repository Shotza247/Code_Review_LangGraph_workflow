from pathlib import Path

from ..config import ROOT


def load_skill(name: str) -> str:
    """Load one local skill's instruction body without frontmatter."""
    path = ROOT / "skills" / name / "SKILL.md"
    raw = path.read_text(encoding="utf-8")
    body = raw
    if raw.startswith("---"):
        _, _, body = raw.split("---", 2)
    instructions = body.strip()
    if not instructions:
        raise ValueError(f"Skill file has no instructions: {path}")
    return instructions
