from pathlib import Path

from ..config import ROOT


def load_skill(name: str) -> dict:
    """Load skills/<name>/SKILL.md (frontmatter stripped) plus any templates/*.md."""
    base = ROOT / "skills" / name
    raw = (base / "SKILL.md").read_text()
    body = raw
    if raw.startswith("---"):
        _, _, body = raw.split("---", 2)
    templates = {p.name: p.read_text() for p in sorted((base / "templates").glob("*.md"))}
    return {"instructions": body.strip(), "templates": templates}
