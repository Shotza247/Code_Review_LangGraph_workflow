import json
import re

from ..utils.chains import compact_json, generate_prompt
from ..utils.json_utils import strip_outer_fence
from ..utils.outputs import save_text

COURSE_PLAN_LINK = "<!-- COURSE_PLAN_LINK -->"


def _ensure_course_plan_marker(readme: str) -> str:
    if COURSE_PLAN_LINK in readme:
        return readme

    heading = "## Learn the codebase"
    match = re.search(r"(?mi)^## Learn the codebase\s*$", readme)
    if match:
        next_heading = re.search(r"(?m)^#{1,6}\s+", readme[match.end():])
        insertion = match.end() + next_heading.start() if next_heading else len(readme)
        return readme[:insertion].rstrip() + f"\n\n{COURSE_PLAN_LINK}\n" + readme[insertion:]

    return readme.rstrip() + f"\n\n{heading}\n\n{COURSE_PLAN_LINK}\n"


def make_readme_sync(ctx):
    def readme_sync_node(state: dict) -> dict:
        readme = strip_outer_fence(
            generate_prompt(
                ctx.llm,
                "readme_sync",
                readme=state["readme_original"] or "(no README)",
                gap_report=json.dumps(state["gap_report"], indent=2),
                code_summary=state.get("code_summary", "")[:5000],
                repository_evidence=compact_json(
                    {
                        "code_review": state.get("code_review", {}),
                        "reproducibility_report": state.get("reproducibility_report", {}),
                        "code_understanding": state.get("code_understanding", {}),
                    },
                    max_items=3,
                    max_string=240,
                ),
            )
        )
        readme = _ensure_course_plan_marker(readme)
        save_text(state["output_dir"], "README.draft.md", readme)
        return {"readme_draft": readme}

    return readme_sync_node
