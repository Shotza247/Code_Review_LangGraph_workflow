"""Streamlit UI. Run with:  streamlit run app.py"""
import difflib
import html
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).parent / "src"))

from readme_sync.config import load_rubric, load_settings  # noqa: E402
from readme_sync.github.client import GitHubClient  # noqa: E402
from readme_sync.github.url import parse_repo_url  # noqa: E402
from readme_sync.graph import build_context  # noqa: E402
from readme_sync.llm.factory import build_llm  # noqa: E402
from readme_sync.nodes.open_pr import make_open_pr  # noqa: E402
from readme_sync.runner import NODE_LABELS, stream_run  # noqa: E402
from readme_sync.utils.outputs import zip_dir  # noqa: E402

st.set_page_config(page_title="README Sync Workflow", page_icon="📘", layout="wide")


def mermaid_html(code: str) -> str:
    return (
        f'<pre class="mermaid">{html.escape(code)}</pre>'
        "<script type=\"module\">"
        "import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';"
        "mermaid.initialize({startOnLoad:true});</script>"
    )


# ------------------------------------------------------------------ sidebar
base = load_settings()
with st.sidebar:
    st.header("Settings")
    provider = st.selectbox("LLM provider", ["huggingface", "openai"], index=0)
    model = st.text_input("Model", base["llm"][provider]["model"], key=f"model_{provider}")
    api_key = st.text_input(
        f"{'HF' if provider == 'huggingface' else 'OpenAI'} API key",
        type="password",
        help="Leave empty to use the key from your .env file. Held in this session only.",
    )
    gh_token = st.text_input(
        "GitHub token (optional)",
        type="password",
        help="Raises the API rate limit. Required only for opening a pull request.",
    )
    st.caption("Repo code is read through the GitHub REST API. Nothing is written to GitHub until you open a PR.")

# ------------------------------------------------------------------ main
st.title("README Sync Workflow")
st.write("Paste a public GitHub repo. The workflow audits its README, checks it against the code, and drafts a better one.")

repo_url = st.text_input("GitHub repo URL", placeholder="https://github.com/owner/repo")
run = st.button("Run workflow", type="primary", disabled=not repo_url.strip())

if run:
    st.session_state.pop("result", None)
    try:
        parse_repo_url(repo_url)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    settings = load_settings(overrides={"llm.provider": provider, "pr.mode": "off"})
    settings["llm"][provider]["model"] = model
    try:
        llm = build_llm(settings, api_key=api_key or None)
        gh = GitHubClient(token=gh_token or None)
        state: dict = {}
        with st.status("Running...", expanded=True) as status:
            for node, state in stream_run(settings, repo_url.strip(), llm=llm, gh=gh):
                st.write(f"Done: {NODE_LABELS[node]}")
            status.update(label="Finished", state="complete", expanded=False)
        st.session_state["result"] = state
        st.session_state["settings"] = settings
        st.session_state["gh"] = gh
    except Exception as exc:  # surface any node failure instead of a stack trace
        st.error(f"Run failed: {exc}")

# ------------------------------------------------------------------ results
result = st.session_state.get("result")
if result:
    v1, v2 = result["readme_rating_v1"]["score"], result["readme_rating_v2"]["score"]
    c1, c2, c3 = st.columns(3)
    c1.metric("README rating (README only)", f"{v1}/100")
    c2.metric("Rating after code gap analysis", f"{v2}/100", delta=v2 - v1)
    c3.metric("Diagrams", len(result.get("diagrams", {})))
    for msg in result.get("errors", []):
        st.warning(msg)

    t_rate, t_gap, t_analysis, t_readme, t_course, t_diag, t_pr = st.tabs(
        ["Ratings", "Gaps", "Code analysis", "New README", "Course plan", "Diagrams", "Pull request"]
    )

    with t_rate:
        rows = [
            {
                "criterion": cid,
                "max": c["max"],
                "README only": c["score"],
                "with code analysis": result["readme_rating_v2"]["criteria"][cid]["score"],
                "note (code analysis)": result["readme_rating_v2"]["criteria"][cid]["note"],
            }
            for cid, c in result["readme_rating_v1"]["criteria"].items()
        ]
        st.dataframe(rows, use_container_width=True, hide_index=True)
        st.write(result["readme_rating_v2"].get("summary", ""))

    with t_gap:
        gaps = result["gap_report"]
        st.subheader("Missing from the README")
        st.dataframe(gaps.get("missing", []), use_container_width=True, hide_index=True)
        if gaps.get("inaccurate"):
            st.subheader("Inaccurate")
            st.dataframe(gaps["inaccurate"], use_container_width=True, hide_index=True)
        with st.expander("Codebase summary used for the analysis"):
            st.markdown(result["code_summary"])

    with t_analysis:
        review = result["code_review"]
        reproducibility = result["reproducibility_report"]
        understanding = result["code_understanding"]
        a1, a2, a3 = st.columns(3)
        a1.metric("Files sampled", len(result.get("sampled_files", [])))
        a2.metric("Code review findings", len(review.get("findings", [])))
        a3.metric("Reproducibility", reproducibility.get("status", "unknown").title())
        st.caption(review.get("scope_note", "Static review only; repository code was not executed."))

        st.subheader("Code review")
        if review.get("findings"):
            st.dataframe(review["findings"], use_container_width=True, hide_index=True)
        else:
            st.info("No actionable findings were identified in the sampled files.")
        if review.get("strengths"):
            st.markdown("**Strengths**")
            st.write(review["strengths"])
        if review.get("test_gaps"):
            st.markdown("**Testing gaps**")
            st.write(review["test_gaps"])

        st.subheader("Reproducibility")
        st.caption(reproducibility.get("scope_note", "Commands were identified from repository files and not executed."))
        for key, title in [
            ("prerequisites", "Prerequisites"),
            ("setup_commands", "Setup commands"),
            ("run_commands", "Run commands"),
            ("test_commands", "Test commands"),
            ("configuration", "Configuration"),
            ("verification", "Verification"),
            ("gaps", "Reproducibility gaps"),
        ]:
            if reproducibility.get(key):
                with st.expander(title, expanded=key == "gaps"):
                    st.write(reproducibility[key])

        st.subheader("Architecture and data flow")
        st.write(understanding.get("main_flow", "Unknown"))
        if understanding.get("components"):
            st.dataframe(understanding["components"], use_container_width=True, hide_index=True)
        st.markdown(f"**Data flow:** {understanding.get('data_flow', 'Unknown')}")
        if understanding.get("unknowns"):
            st.markdown("**Unknowns**")
            st.write(understanding["unknowns"])

    with t_readme:
        view = st.radio("View", ["Rendered", "Diff vs original", "Markdown source"], horizontal=True)
        if view == "Rendered":
            st.markdown(result["readme_synced"])
        elif view == "Diff vs original":
            diff = difflib.unified_diff(
                result["readme_original"].splitlines(),
                result["readme_synced"].splitlines(),
                "README (original)",
                "README (new)",
                lineterm="",
            )
            st.code("\n".join(diff) or "No changes", language="diff")
        else:
            st.code(result["readme_synced"], language="markdown")
        st.download_button("Download README.new.md", result["readme_synced"], file_name="README.new.md")

    with t_course:
        st.markdown(result["course_plan"])
        st.download_button("Download course_plan.md", result["course_plan"], file_name="course_plan.md")

    with t_diag:
        svgs = result.get("diagram_svgs", {})
        if not result.get("diagrams"):
            st.info("No diagrams were produced. See the warnings above.")
        for name, code in result.get("diagrams", {}).items():
            st.subheader(name.replace("_", " ").title())
            markdown_block = f"```mermaid\n{code}\n```"
            if name in svgs and Path(svgs[name]).exists():
                st.image(svgs[name])  # rendered and validated with mmdc
                with st.expander("README Mermaid block"):
                    st.markdown(markdown_block)
            else:
                st.markdown(markdown_block)
            with st.expander("Mermaid source"):
                st.code(code, language="text")

    with t_pr:
        if result.get("pr_url"):
            st.success(f"Pull request opened: {result['pr_url']}")
        else:
            st.write("Review the outputs first. Opening a PR writes to GitHub.")
            mode = st.radio(
                "How should the PR be opened?",
                ["fork", "direct"],
                format_func=lambda m: "Fork the repo, push a branch there, open a PR (any public repo)"
                if m == "fork"
                else "Push a branch to the repo itself, then open a PR (needs push access)",
            )
            gh = st.session_state["gh"]
            if not gh.token:
                st.info("Add a GitHub token in the sidebar (and re-run) to enable this step.")
            confirm = st.checkbox("I reviewed the new README and want to open a pull request")
            if st.button("Open pull request", disabled=not (gh.token and confirm)):
                try:
                    settings = dict(st.session_state["settings"])
                    settings["pr"] = {**settings["pr"], "mode": mode}
                    ctx = build_context(settings, llm=object(), gh=gh, rubric=load_rubric())
                    update = make_open_pr(ctx)(result)
                    result.update(update)
                    st.session_state["result"] = result
                    st.rerun()
                except Exception as exc:
                    st.error(f"Could not open the PR: {exc}")

    st.divider()
    st.download_button(
        "Download all outputs (.zip)",
        zip_dir(result["output_dir"]),
        file_name=f"{result['owner']}__{result['repo']}.zip",
    )
