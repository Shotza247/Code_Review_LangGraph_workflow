import copy
from pathlib import Path

from readme_sync.config import load_settings
from readme_sync.runner import stream_run
from readme_sync.utils.outputs import zip_dir

from fakes import FakeGH, FakeLLM


def test_stream_run_order_and_state(tmp_path):
    s = copy.deepcopy(load_settings(overrides={"pr.mode": "off"}))
    s["outputs_dir"] = str(tmp_path)
    s["mermaid_validation"] = {"mode": "off"}
    steps = list(stream_run(s, "https://github.com/o/r", llm=FakeLLM(), gh=FakeGH()))
    assert [n for n, _ in steps] == ["readme_audit", "codebase_analysis", "course_plan", "readme_sync", "diagrams"]
    final = steps[-1][1]
    assert final["readme_rating_v1"]["score"] == 40 and "diagrams" in final
    assert zip_dir(final["output_dir"])[:2] == b"PK"


def test_app_first_render_has_no_errors():
    from streamlit.testing.v1 import AppTest

    app_path = Path(__file__).resolve().parents[1] / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=30).run()
    assert not at.exception
    assert any("README Sync" in t.value for t in at.title)


def test_app_full_run_then_pr_gate(monkeypatch):
    import shutil

    from streamlit.testing.v1 import AppTest

    import readme_sync.github.client as client_mod
    import readme_sync.config as config_mod
    import readme_sync.llm.factory as factory_mod

    class AppGH(FakeGH):
        def __init__(self, token=None):
            super().__init__()
            self.token = token

    monkeypatch.setattr(factory_mod, "build_llm", lambda settings, api_key=None: FakeLLM())
    monkeypatch.setattr(client_mod, "GitHubClient", AppGH)
    load_settings = config_mod.load_settings

    def settings_without_external_rendering(*args, **kwargs):
        settings = load_settings(*args, **kwargs)
        settings["mermaid_validation"] = {"mode": "off"}
        return settings

    monkeypatch.setattr(config_mod, "load_settings", settings_without_external_rendering)

    app_path = Path(__file__).resolve().parents[1] / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=60).run()
    url_box = [t for t in at.text_input if t.label == "GitHub repo URL"][0]
    url_box.set_value("https://github.com/o/r").run()
    at.button[0].click().run()
    try:
        assert not at.exception, at.exception
        assert not at.error, [e.value for e in at.error]
        labels = [m.label for m in at.metric]
        assert "README rating (README only)" in labels and "Diagrams" in labels
        assert len(at.tabs) == 7
        # PR button must be disabled: no token and no confirmation
        pr_btn = [b for b in at.button if b.label == "Open pull request"][0]
        assert pr_btn.proto.disabled
    finally:
        shutil.rmtree(Path(__file__).resolve().parents[1] / "outputs" / "o__r", ignore_errors=True)
