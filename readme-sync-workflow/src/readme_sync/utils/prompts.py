from pathlib import Path
from string import Template

PROMPT_DIR = Path(__file__).resolve().parents[1] / "prompts"
SYSTEM = "You are a precise software documentation engineer. Never invent facts that are not in the provided material."


def render(name: str, **values: str) -> str:
    # $placeholders (string.Template) so JSON braces in prompts need no escaping
    return Template((PROMPT_DIR / f"{name}.md").read_text()).safe_substitute(**values)
