import re

from ..utils.chains import compact_json, generate_prompt
from ..utils.outputs import save_text
from ..utils.skill_loader import load_skill


def make_course_plan(ctx):
    skill = load_skill("codebase-to-interactive-course")
    max_lines = ctx.settings["github"]["max_tree_lines"]

    def course_plan_node(state: dict) -> dict:
        assessment = {
            "gap_report": state["gap_report"],
            "code_review": state["code_review"],
            "reproducibility_report": state["reproducibility_report"],
            "code_understanding": state["code_understanding"],
        }
        source = generate_prompt(
            ctx.llm,
            "interactive_course",
            skill_instructions=skill["instructions"],
            tree="\n".join(state["file_tree"][:max_lines])[:4000],
            code_summary=state["code_summary"][:2500],
            assessment=compact_json(assessment),
        )
        headings = list(re.finditer(r"(?m)^## Lesson \d+:\s*(.+?)\s*$", source))
        if not headings:
            raise ValueError("Interactive course response did not contain lesson headings")

        output_dir = state["output_dir"]
        lesson_dir = "docs/interactive-course/lessons"
        intro = source[:headings[0].start()].strip()
        links = []
        lesson_paths = []
        for index, heading in enumerate(headings):
            title = heading.group(1).strip()
            end = headings[index + 1].start() if index + 1 < len(headings) else len(source)
            content = source[heading.start():end].strip()
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or f"lesson-{index + 1}"
            filename = f"{index + 1:02d}-{slug}.md"
            relative_path = f"{lesson_dir}/{filename}"
            save_text(output_dir, relative_path, content + "\n")
            lesson_paths.append(relative_path)
            links.append(f"- [Lesson {index + 1}: {title}](lessons/{filename})")

        index = f"{intro}\n\n## Course navigation\n\n" + "\n".join(links) + "\n"
        index_path = "docs/interactive-course/index.md"
        save_text(output_dir, index_path, index)
        plan_path = "docs/interactive-course/index.md"
        return {
            "course_mode": "interactive",
            "course_plan": index,
            "course_plan_path": plan_path,
            "interactive_course": {"index": index_path, "lessons": lesson_paths},
        }

    return course_plan_node
