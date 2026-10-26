import copy
import subprocess
from types import SimpleNamespace

import pytest

from readme_sync.config import load_settings
from readme_sync.graph import build_graph
from readme_sync.utils import mermaid
from readme_sync.utils.mermaid import MermaidToolError, ValidationResult, validate_mermaid

from fakes import FakeGH, FakeLLM

CODE = "flowchart TD\n A-->B"


def _run(returncode=0, stderr=""):
    return lambda *a, **k: SimpleNamespace(returncode=returncode, stderr=stderr, stdout="")


def test_off_mode_skips(tmp_path):
    r = validate_mermaid(CODE, tmp_path / "a.svg", {"mode": "off"})
    assert r.ok and not r.validated


def test_missing_mmdc_auto_vs_required(tmp_path, monkeypatch):
    monkeypatch.setattr(mermaid.shutil, "which", lambda _n: None)
    r = validate_mermaid(CODE, tmp_path / "a.svg", {"mode": "auto"})
    assert r.ok and not r.validated and not r.note
    with pytest.raises(MermaidToolError):
        validate_mermaid(CODE, tmp_path / "a.svg", {"mode": "required"})


def test_valid_render(tmp_path, monkeypatch):
    monkeypatch.setattr(mermaid.shutil, "which", lambda _n: "/bin/mmdc")
    monkeypatch.setattr(mermaid.subprocess, "run", _run(0))
    r = validate_mermaid(CODE, tmp_path / "a.svg", {"mode": "auto"})
    assert r.ok and r.validated and r.svg_path


def test_parse_error_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(mermaid.shutil, "which", lambda _n: "/bin/mmdc")
    monkeypatch.setattr(mermaid.subprocess, "run", _run(1, "Parse error on line 2"))
    r = validate_mermaid(CODE, tmp_path / "a.svg", {"mode": "auto"})
    assert not r.ok and r.validated and "Parse error" in r.error


def test_browser_launch_failure_is_not_a_diagram_error(tmp_path, monkeypatch):
    monkeypatch.setattr(mermaid.shutil, "which", lambda _n: "/bin/mmdc")
    monkeypatch.setattr(mermaid.subprocess, "run", _run(1, "Error: Failed to launch the browser process"))
    r = validate_mermaid(CODE, tmp_path / "a.svg", {"mode": "auto"})
    assert r.ok and not r.validated and "puppeteer_config" in r.note
    with pytest.raises(MermaidToolError):
        validate_mermaid(CODE, tmp_path / "a.svg", {"mode": "required"})


def test_timeout(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise subprocess.TimeoutExpired("mmdc", 1)

    monkeypatch.setattr(mermaid.shutil, "which", lambda _n: "/bin/mmdc")
    monkeypatch.setattr(mermaid.subprocess, "run", boom)
    assert not validate_mermaid(CODE, tmp_path / "a.svg", {"mode": "auto"}).ok


def _settings(tmp_path, max_repairs=2):
    s = copy.deepcopy(load_settings(overrides={"pr.mode": "off"}))
    s["outputs_dir"] = str(tmp_path)
    s["mermaid_validation"] = {"mode": "auto", "max_repairs": max_repairs}
    return s


def test_repair_loop_fixes_diagram(tmp_path, monkeypatch):
    seen = {}

    def fake_validate(code, svg_path, cfg):
        key = str(svg_path)
        seen[key] = seen.get(key, 0) + 1
        if seen[key] == 1:  # fail the first time per diagram
            return ValidationResult(ok=False, validated=True, error="Parse error")
        return ValidationResult(ok=True, validated=True, svg_path=key)

    monkeypatch.setattr("readme_sync.nodes.diagrams.validate_mermaid", fake_validate)
    llm = FakeLLM()
    result = build_graph(_settings(tmp_path), llm=llm, gh=FakeGH()).invoke({"repo_url": "https://github.com/o/r"})
    assert len(result["diagrams"]) == 3 and len(result["diagram_svgs"]) == 3
    assert llm.tasks.count("diagram_repair") == 3
    assert not result["errors"]


def test_unfixable_diagram_is_skipped(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "readme_sync.nodes.diagrams.validate_mermaid",
        lambda *a, **k: ValidationResult(ok=False, validated=True, error="Parse error"),
    )
    llm = FakeLLM()
    result = build_graph(_settings(tmp_path, max_repairs=1), llm=llm, gh=FakeGH()).invoke(
        {"repo_url": "https://github.com/o/r"}
    )
    assert result["diagrams"] == {}
    assert sum("still invalid" in e for e in result["errors"]) == 3
    assert llm.tasks.count("diagram_repair") == 3  # one repair per diagram, then give up
    assert "```mermaid" not in result["readme_synced"]


def test_missing_mmdc_auto_does_not_warn(tmp_path, monkeypatch):
    monkeypatch.setattr("readme_sync.utils.mermaid.shutil.which", lambda _n: None)
    result = build_graph(_settings(tmp_path), llm=FakeLLM(), gh=FakeGH()).invoke(
        {"repo_url": "https://github.com/o/r"}
    )
    assert len(result["diagrams"]) == 3
    assert not any("mmdc not found" in e for e in result["errors"])
