from ..utils.chains import compact_json, generate_prompt
from ..utils.outputs import save_text


def make_course_guide(ctx):
    plan_path = ctx.settings["pr"]["course_plan_path"]

    def course_guide_node(state: dict) -> dict:
        guide = generate_prompt(
            ctx.llm,
            "course_guide",
            code_summary=state["code_summary"][:2500],
            reproducibility_report=compact_json(state["reproducibility_report"], max_items=1),
            code_understanding=compact_json(state["code_understanding"], max_items=1),
            gap_report=compact_json(state["gap_report"], max_items=1),
        )
        save_text(state["output_dir"], "step_by_step_guide.md", guide)
        save_text(state["output_dir"], "course_plan.md", guide)
        return {
            "course_mode": "guide",
            "course_plan": guide,
            "course_plan_path": plan_path,
            "step_by_step_guide": guide,
        }

    return course_guide_node
