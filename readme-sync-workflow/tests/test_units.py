import pytest

from readme_sync.github.url import parse_repo_url
from readme_sync.nodes.diagrams import _extract_mermaid, splice_diagrams
from readme_sync.utils.files import select_files
from readme_sync.utils.json_utils import extract_json, strip_outer_fence
from readme_sync.utils.rating import normalize_rating
from readme_sync.config import load_rubric
from readme_sync.nodes.course_guide import _validate_study_plan
from readme_sync.utils.skill_loader import load_skill


def test_parse_url():
    assert parse_repo_url("https://github.com/a/b.git").repo == "b"
    assert parse_repo_url("github.com/a/b/tree/main").owner == "a"
    with pytest.raises(ValueError):
        parse_repo_url("https://gitlab.com/a/b")


def test_extract_json_fenced_and_noisy():
    assert extract_json('Sure!\n```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('blah {"a": 2} blah') == {"a": 2}


def test_strip_outer_fence():
    assert strip_outer_fence("```markdown\n# Hi\n```") == "# Hi"


def test_normalize_clamps_and_sums():
    rubric = load_rubric()
    r = normalize_rating({"criteria": {"install": {"score": 999}}}, rubric)
    assert r["criteria"]["install"]["score"] == 20 and r["score"] == 20


def test_select_files_skips_binaries_and_prefers_manifests():
    tree = [{"path": "logo.png", "size": 1}, {"path": "src/a.py", "size": 1},
            {"path": "requirements.txt", "size": 1}, {"path": "node_modules/x.js", "size": 1}]
    assert select_files(tree, 10)[0] == "requirements.txt"
    assert "logo.png" not in select_files(tree, 10) and "node_modules/x.js" not in select_files(tree, 10)


def test_load_skill_strips_frontmatter_and_returns_instructions_only(tmp_path, monkeypatch):
    skill_dir = tmp_path / "skills" / "example"
    skill_dir.mkdir(parents=True)
    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text("---\nname: example\n---\n# Example skill\n\nUse evidence.\n", encoding="utf-8")
    (skill_dir / "templates").mkdir()
    (skill_dir / "templates" / "unused.md").write_text("Not part of the skill prompt.", encoding="utf-8")
    monkeypatch.setattr("readme_sync.utils.skill_loader.ROOT", tmp_path)

    assert load_skill("example") == "# Example skill\n\nUse evidence."


def test_study_plan_requires_five_to_eight_steps_with_checkpoints():
    plan = "\n".join(
        f"{i}. **Action:** Inspect the next area.\n   **Checkpoint:** Explain what you found."
        for i in range(1, 6)
    )
    _validate_study_plan(plan)

    with pytest.raises(ValueError, match="5-8 numbered steps"):
        _validate_study_plan("1. **Action:** Inspect the project.\n   **Checkpoint:** Summarize it.")


def test_mermaid_validation_and_splice():
    assert _extract_mermaid("```mermaid\nflowchart TD\nA-->B\n```") == "flowchart TD\nA-->B"
    assert _extract_mermaid("not a diagram") is None
    out = splice_diagrams("x\n<!-- DIAGRAMS:START -->\n<!-- DIAGRAMS:END -->", [("T", "flowchart TD\nA-->B")])
    assert "```mermaid" in out and out.count("DIAGRAMS:START") == 1
