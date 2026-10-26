import json
import re

from readme_sync.llm.base import LLMAdapter

RATING = {
    "criteria": {c: {"score": 5, "note": "ok"} for c in
                 ["overview", "prerequisites", "install", "configuration", "run",
                  "expected_output", "verification", "troubleshooting"]},
    "strengths": ["x"], "weaknesses": ["y"], "summary": "s",
}
MERMAID = "```mermaid\nflowchart TD\n  A[main.py] --> B[utils.py]\n```"


class FakeLLM(LLMAdapter):
    """Returns canned output keyed on the TASK: line at the top of each prompt."""

    def __init__(self):
        self.tasks = []
        self.prompts = []

    def _complete(self, prompt, system):
        match = re.search(r"^TASK:(.+)$", prompt, re.MULTILINE)
        if not match:
            raise AssertionError("Prompt is missing its TASK identifier")
        task = match.group(1).strip()
        self.tasks.append(task)
        self.prompts.append(prompt)
        return {
            "readme_audit": json.dumps(RATING),
            "code_map": "- main.py: entry point",
            "code_reduce": "## Purpose\nDemo app",
            "repository_assessment": json.dumps({
                "gap_report": {
                    "missing": [{"item": "install", "evidence": "requirements.txt", "severity": "high"}],
                    "inaccurate": [],
                    "covered_well": [],
                },
                "code_review": {
                    "findings": [],
                    "strengths": ["Application entry point is identifiable."],
                    "test_gaps": ["No test files were sampled."],
                    "scope_note": "Static review only; no code or tests were executed.",
                },
                "reproducibility_report": {
                    "status": "partial",
                    "prerequisites": [],
                    "setup_commands": [],
                    "run_commands": [],
                    "test_commands": [],
                    "configuration": [],
                    "verification": [],
                    "gaps": ["Setup instructions need confirmation."],
                    "scope_note": "Commands were not executed.",
                },
                "code_understanding": {
                    "main_flow": "main.py is the entry point.",
                    "components": [],
                    "data_flow": "Unknown",
                    "unknowns": ["Data flow is not established by sampled files."],
                },
            }),
            "gap_analysis": json.dumps({
                "missing": [{"item": "install", "evidence": "requirements.txt", "severity": "high"}],
                "inaccurate": [],
                "covered_well": [],
            }),
            "readme_rerate": "```json\n" + json.dumps(RATING) + "\n```",  # fenced on purpose
            "course_plan": "# Course plan: demo",
            "readme_sync": "# Demo\n\n## Project structure\n\n<!-- DIAGRAMS:START -->\n<!-- DIAGRAMS:END -->\n",
            "diagram": MERMAID,
            "diagram_repair": MERMAID,
        }[task]


class FakeGH:
    token = "fake"

    def __init__(self):
        self.calls = []

    def get_repo(self, o, r):
        return {"default_branch": "main"}

    def get_readme(self, o, r, ref):
        return "README.md", "# Demo\nrun it"

    def get_tree(self, o, r, ref):
        return [{"path": "main.py", "size": 10}, {"path": "requirements.txt", "size": 5},
                {"path": "logo.png", "size": 99}]

    def get_file_text(self, o, r, path, ref):
        return "print('hi')"

    def get_branch_sha(self, o, r, b):
        return "abc"

    def fork_repo(self, o, r):
        self.calls.append("fork")
        return "me"

    def create_branch(self, o, r, name, sha):
        self.calls.append(f"branch:{o}")

    def put_file(self, o, r, path, text, msg, branch):
        self.calls.append(f"put:{path}")

    def open_pull_request(self, o, r, title, body, head, base):
        self.calls.append(f"pr:{head}")
        return "https://github.com/o/r/pull/1"
