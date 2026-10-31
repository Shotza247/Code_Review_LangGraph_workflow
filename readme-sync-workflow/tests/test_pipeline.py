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


def test_dry_run_produces_artifacts_and_no_pr(tmp_path, monkeypatch):
    from importlib import import_module

    guide_module = import_module("readme_sync.nodes.course_guide")
    interactive_module = import_module("readme_sync.nodes.course_plan")
    loaded_skills = []
    guide_loader = guide_module.load_skill
    interactive_loader = interactive_module.load_skill

    def track_guide_skill(name):
        loaded_skills.append(name)
        return guide_loader(name)

    def track_interactive_skill(name):
        loaded_skills.append(name)
        return interactive_loader(name)

    monkeypatch.setattr(guide_module, "load_skill", track_guide_skill)
    monkeypatch.setattr(interactive_module, "load_skill", track_interactive_skill)

    gh = FakeGH()
    llm = FakeLLM()
    result = build_graph(_settings(tmp_path, "off"), llm=llm, gh=gh).invoke(
        {"repo_url": "https://github.com/o/r"}
    )
    assert result["readme_rating_v1"]["score"] == 40
    assert result["code_review"]["scope_note"].startswith("Static review")
    assert result["reproducibility_report"]["status"] == "partial"
    assert result["code_understanding"]["main_flow"]
    assert result["assessment_complete"] is True
    assert llm.tasks.count("repository_assessment") == 1
    assert result["course_mode"] == "guide"
    assert llm.tasks.count("course_guide") == 1
    assert llm.tasks.count("interactive_course") == 0
    assert loaded_skills == ["codebase-to-course", "codebase-to-study-plan"]
    guide_prompt = llm.prompts[llm.tasks.index("course_guide")]
    assert "SHARED LEARNING-DESIGN SKILL" in guide_prompt
    assert "Give 5-8 numbered steps" in guide_prompt
    assert "INTERACTIVE-COURSE SKILL" not in guide_prompt
    assert llm.tasks.index("readme_sync") < llm.tasks.index("course_guide")
    assert "Demo app" in llm.prompts[llm.tasks.index("readme_sync")]
    assert "[Step-by-step study plan](docs/COURSE_PLAN.md)" in result["readme_synced"]
    assert "<!-- COURSE_PLAN_LINK -->" not in result["readme_synced"]
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
        "README.draft.md",
        "README.new.md",
        "docs/COURSE_PLAN.md",
        "run_summary.json",
        "audit_log.json",
        "step_by_step_guide.md",
    ]:
        assert (out / f).exists(), f


def test_interactive_course_branch_writes_linked_lessons(tmp_path, monkeypatch):
    from importlib import import_module

    guide_module = import_module("readme_sync.nodes.course_guide")
    interactive_module = import_module("readme_sync.nodes.course_plan")
    loaded_skills = []
    guide_loader = guide_module.load_skill
    interactive_loader = interactive_module.load_skill

    def track_guide_skill(name):
        loaded_skills.append(name)
        return guide_loader(name)

    def track_interactive_skill(name):
        loaded_skills.append(name)
        return interactive_loader(name)

    monkeypatch.setattr(guide_module, "load_skill", track_guide_skill)
    monkeypatch.setattr(interactive_module, "load_skill", track_interactive_skill)

    llm = FakeLLM()
    result = build_graph(_settings(tmp_path, "off"), llm=llm, gh=FakeGH()).invoke(
        {"repo_url": "https://github.com/o/r", "course_mode": "interactive"}
    )
    assert result["course_mode"] == "interactive"
    assert llm.tasks.count("interactive_course") == 1
    assert llm.tasks.count("course_guide") == 0
    assert loaded_skills == ["codebase-to-course", "codebase-to-interactive-course"]
    interactive_prompt = llm.prompts[llm.tasks.index("interactive_course")]
    assert "SHARED LEARNING-DESIGN SKILL" in interactive_prompt
    assert "Return one Markdown course source" in interactive_prompt
    assert "STEP-BY-STEP STUDY-PLAN SKILL" not in interactive_prompt
    assert len(result["interactive_course"]["lessons"]) == 3
    assert all((tmp_path / "o__r" / path).exists() for path in result["interactive_course"]["lessons"])
    assert "[Lesson 1: Repository map](lessons/01-repository-map.md)" in result["course_plan"]
    assert "[Interactive course](docs/interactive-course/index.md)" in result["readme_synced"]


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


def test_empty_code_summary_uses_mapped_evidence(tmp_path):
    class EmptySummaryLLM(FakeLLM):
        def _complete(self, prompt, system):
            if "TASK:code_reduce" in prompt:
                self.tasks.append("code_reduce")
                self.prompts.append(prompt)
                return "  "
            return super()._complete(prompt, system)

    result = build_graph(_settings(tmp_path, "off"), llm=EmptySummaryLLM(), gh=FakeGH()).invoke(
        {"repo_url": "https://github.com/o/r"}
    )
    assert "main.py: entry point" in result["code_summary"]
    assert any("using mapped repository evidence" in error for error in result["errors"])


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


def test_interactive_course_files_are_included_in_pr(tmp_path):
    gh = FakeGH()
    result = build_graph(_settings(tmp_path, "fork"), llm=FakeLLM(), gh=gh).invoke(
        {"repo_url": "https://github.com/o/r", "course_mode": "interactive"}
    )
    assert result["course_plan_path"] == "docs/interactive-course/index.md"
    assert "put:docs/interactive-course/index.md" in gh.calls
    assert any(call.startswith("put:docs/interactive-course/lessons/") for call in gh.calls)
