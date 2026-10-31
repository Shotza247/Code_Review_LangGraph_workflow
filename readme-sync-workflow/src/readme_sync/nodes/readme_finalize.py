import re
from pathlib import Path

from ..utils.outputs import save_text
from .readme_sync import COURSE_PLAN_LINK

REQUIRED_SECTIONS = (
    "Overview",
    "Prerequisites",
    "Installation",
    "Configuration",
    "Usage",
    "Expected output",
    "Verify your setup",
    "Project structure",
    "Learn the codebase",
    "Troubleshooting",
)


def make_readme_finalize():
    def readme_finalize_node(state: dict) -> dict:
        draft = state.get("readme_draft", "")
        if COURSE_PLAN_LINK not in draft:
            raise ValueError("README draft is missing its course-plan link marker")

        heading_positions = []
        missing_sections = []
        for section in REQUIRED_SECTIONS:
            match = re.search(rf"(?mi)^## {re.escape(section)}\s*$", draft)
            if match:
                heading_positions.append(match.start())
            else:
                missing_sections.append(section)
        if missing_sections:
            raise ValueError(f"README draft is missing required sections: {', '.join(missing_sections)}")
        if heading_positions != sorted(heading_positions):
            raise ValueError("README draft sections are not in the required order")

        course_plan_path = state["course_plan_path"].replace("\\", "/")
        output_dir = Path(state["output_dir"])
        artifact_path = output_dir / course_plan_path
        if not artifact_path.is_file() or not artifact_path.read_text(encoding="utf-8").strip():
            raise FileNotFoundError(f"Generated learning artifact is missing or empty: {artifact_path}")

        missing_lessons = [
            path
            for path in state.get("interactive_course", {}).get("lessons", [])
            if not (output_dir / path).is_file()
        ]
        if missing_lessons:
            raise FileNotFoundError(f"Generated course lessons are missing: {', '.join(missing_lessons)}")

        label = (
            "Interactive course"
            if state.get("course_mode") == "interactive"
            else "Step-by-step study plan"
        )
        link = f"- [{label}]({course_plan_path})"
        readme = draft.replace(COURSE_PLAN_LINK, link)
        if COURSE_PLAN_LINK in readme:
            raise ValueError("README finalization left an unresolved course-plan link marker")
        if f"]({course_plan_path})" not in readme:
            raise ValueError("Final README does not link to the selected learning artifact")

        save_text(output_dir, "README.new.md", readme)
        return {"readme_synced": readme}

    return readme_finalize_node
