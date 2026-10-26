import pytest

from readme_sync.github.url import parse_repo_url
from readme_sync.nodes.diagrams import _extract_mermaid, splice_diagrams
from readme_sync.utils.files import select_files
from readme_sync.utils.json_utils import extract_json, strip_outer_fence
from readme_sync.utils.rating import normalize_rating
from readme_sync.config import load_rubric


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


def test_mermaid_validation_and_splice():
    assert _extract_mermaid("```mermaid\nflowchart TD\nA-->B\n```") == "flowchart TD\nA-->B"
    assert _extract_mermaid("not a diagram") is None
    out = splice_diagrams("x\n<!-- DIAGRAMS:START -->\n<!-- DIAGRAMS:END -->", [("T", "flowchart TD\nA-->B")])
    assert "```mermaid" in out and out.count("DIAGRAMS:START") == 1
