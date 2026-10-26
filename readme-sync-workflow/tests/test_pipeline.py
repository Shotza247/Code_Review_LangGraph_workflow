import copy

from readme_sync.config import load_settings
from readme_sync.graph import build_graph

from fakes import FakeGH, FakeLLM


def _settings(tmp_path, mode):
    s = load_settings(overrides={"pr.mode": mode})
    s = copy.deepcopy(s)
    s["outputs_dir"] = str(tmp_path)
    s["mermaid_validation"] = {"mode": "off"}
    return s


def test_dry_run_produces_artifacts_and_no_pr(tmp_path):
    gh = FakeGH()
    llm = FakeLLM()
    result = build_graph(_settings(tmp_path, "off"), llm=llm, gh=gh).invoke(
        {"repo_url": "https://github.com/o/r"}
    )
    assert result["readme_rating_v1"]["score"] == 40
    assert result["code_review"]["scope_note"].startswith("Static review")
    assert result["reproducibility_report"]["status"] == "partial"
    assert result["code_understanding"]["main_flow"]
    assert llm.tasks.count("repository_assessment") == 1
    course_prompt = llm.prompts[llm.tasks.index("course_plan")]
    assert "STATIC CODE REVIEW:" in course_prompt
    assert "REPRODUCIBILITY ASSESSMENT:" in course_prompt
    assert "```mermaid" in result["readme_synced"]
    assert len(result["diagrams"]) == 3
    assert len(result["audit_log"]) >= 5
    assert result["audit_log"][0]["event"] == "node_executed"
    assert result["audit_log"][0]["node"] == "readme_audit"
    assert "pr_url" not in result and gh.calls == []
    out = tmp_path / "o__r"
    for f in [
        "audit.json",
        "gap_report.json",
        "code_review.json",
        "reproducibility_report.json",
        "code_understanding.json",
        "rating_v2.json",
        "course_plan.md",
        "README.new.md",
        "run_summary.json",
        "audit_log.json",
    ]:
        assert (out / f).exists(), f


def test_malformed_repository_assessment_falls_back(tmp_path):
    class BadAssessmentLLM(FakeLLM):
        def _complete(self, prompt, system):
            if "TASK:repository_assessment" in prompt:
                self.tasks.append("repository_assessment")
                self.prompts.append(prompt)
                return '{"gap_report": {"missing": ['
            return super()._complete(prompt, system)

    result = build_graph(_settings(tmp_path, "off"), llm=BadAssessmentLLM(), gh=FakeGH()).invoke(
        {"repo_url": "https://github.com/o/r"}
    )
    assert result["reproducibility_report"]["status"] == "unknown"
    assert result["code_understanding"]["main_flow"] == "Unknown"
    assert any("repository assessment fell back" in err for err in result["errors"])


def test_fork_mode_opens_pr(tmp_path):
    gh = FakeGH()
    result = build_graph(_settings(tmp_path, "fork"), llm=FakeLLM(), gh=gh).invoke(
        {"repo_url": "https://github.com/o/r"}
    )
    assert result["pr_url"].endswith("/pull/1")
    assert "fork" in gh.calls and "pr:me:readme-sync/update" in gh.calls
    assert "put:README.md" in gh.calls and "put:docs/COURSE_PLAN.md" in gh.calls


def test_direct_mode_uses_same_repo(tmp_path):
    gh = FakeGH()
    build_graph(_settings(tmp_path, "direct"), llm=FakeLLM(), gh=gh).invoke({"repo_url": "https://github.com/o/r"})
    assert "fork" not in gh.calls and "branch:o" in gh.calls and "pr:readme-sync/update" in gh.calls
