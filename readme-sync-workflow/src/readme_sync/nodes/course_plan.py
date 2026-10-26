import json

from ..utils.outputs import save_text
from ..utils.prompts import SYSTEM, render
from ..utils.skill_loader import load_skill


def make_course_plan(ctx):
    skill = load_skill("codebase-to-course")
    max_lines = ctx.settings["github"]["max_tree_lines"]

    def course_plan_node(state: dict) -> dict:
        prompt = render(
            "course_plan",
            skill_instructions=skill["instructions"],
            template=skill["templates"].get("course_plan.md", ""),
            tree="\n".join(state["file_tree"][:max_lines]),
            code_summary=state["code_summary"],
            gap_report=json.dumps(state["gap_report"], indent=2),
            code_review=json.dumps(state["code_review"], indent=2),
            reproducibility_report=json.dumps(state["reproducibility_report"], indent=2),
            code_understanding=json.dumps(state["code_understanding"], indent=2),
        )
        plan = ctx.llm.generate(prompt, system=SYSTEM)
        save_text(state["output_dir"], "course_plan.md", plan)
        return {"course_plan": plan}

    return course_plan_node
