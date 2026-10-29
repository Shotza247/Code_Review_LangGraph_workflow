import json

from ..utils.chains import generate_prompt
from ..utils.json_utils import strip_outer_fence
from ..utils.outputs import save_text


def make_readme_sync(ctx):
    default_plan_path = ctx.settings["pr"]["course_plan_path"]

    def readme_sync_node(state: dict) -> dict:
        readme = strip_outer_fence(
            generate_prompt(
                ctx.llm,
                "readme_sync",
                readme=state["readme_original"] or "(no README)",
                gap_report=json.dumps(state["gap_report"], indent=2),
                code_summary=state["code_summary"],
                course_plan=state["course_plan"],
                course_plan_path=state.get("course_plan_path", default_plan_path),
            )
        )
        save_text(state["output_dir"], "README.new.md", readme)
        return {"readme_synced": readme}

    return readme_sync_node
