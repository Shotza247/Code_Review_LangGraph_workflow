import re

from ..utils.chains import compact_json, generate_prompt
from ..utils.outputs import save_text
from ..utils.skill_loader import load_skill


def _validate_study_plan(plan: str) -> None:
    steps = list(re.finditer(r"(?m)^(\d+)\.\s+.+$", plan))
    if not 5 <= len(steps) <= 8:
        raise ValueError(f"Step-by-step study plan must contain 5-8 numbered steps; found {len(steps)}")

    for index, step in enumerate(steps):
        expected_number = index + 1
        if int(step.group(1)) != expected_number:
            raise ValueError("Step-by-step study plan steps must be numbered consecutively from 1")
        end = steps[index + 1].start() if index + 1 < len(steps) else len(plan)
        if not re.search(r"(?im)^\s*(?:\*\*)?Checkpoint(?:\*\*)?:", plan[step.start():end]):
            raise ValueError(f"Study-plan step {expected_number} is missing its checkpoint")


def make_course_guide(ctx):
    plan_path = ctx.settings["pr"]["course_plan_path"]

    def course_guide_node(state: dict) -> dict:
        shared_skill = load_skill("codebase-to-course")
        study_plan_skill = load_skill("codebase-to-study-plan")
        guide = generate_prompt(
            ctx.llm,
            "course_guide",
            shared_skill_instructions=shared_skill,
            mode_skill_instructions=study_plan_skill,
            readme_draft=state.get("readme_draft", "")[:2500],
            code_summary=state.get("code_summary", "")[:2500],
            reproducibility_report=compact_json(state["reproducibility_report"], max_items=1),
            code_understanding=compact_json(state["code_understanding"], max_items=1),
            gap_report=compact_json(state["gap_report"], max_items=1),
        )
        _validate_study_plan(guide)
        save_text(state["output_dir"], "step_by_step_guide.md", guide)
        save_text(state["output_dir"], "course_plan.md", guide)
        save_text(state["output_dir"], plan_path, guide)
        return {
            "course_mode": "guide",
            "course_plan": guide,
            "course_plan_path": plan_path,
            "step_by_step_guide": guide,
        }

    return course_guide_node
