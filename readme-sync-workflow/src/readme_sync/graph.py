from langgraph.graph import END, START, StateGraph

from .config import load_rubric, pr_mode
from .github.client import GitHubClient
from .llm.factory import build_llm
from .nodes.codebase_analysis import make_codebase_analysis
from .nodes.course_guide import make_course_guide
from .nodes.context import Context
from .nodes.course_plan import make_course_plan
from .nodes.diagrams import make_diagrams
from .nodes.open_pr import make_open_pr
from .nodes.readme_audit import make_readme_audit
from .nodes.readme_finalize import make_readme_finalize
from .nodes.readme_sync import make_readme_sync
from .state import RepoState
from .utils.audit import audit_decision, audit_node


def build_context(settings: dict, llm=None, gh=None, rubric=None) -> Context:
    return Context(
        settings=settings,
        llm=llm or build_llm(settings),
        gh=gh or GitHubClient(),
        rubric=rubric or load_rubric(),
    )


def build_graph(settings: dict, llm=None, gh=None, rubric=None):
    ctx = build_context(settings, llm=llm, gh=gh, rubric=rubric)

    graph = StateGraph(RepoState)
    graph.add_node("readme_audit", audit_node("readme_audit", make_readme_audit(ctx)))
    graph.add_node("codebase_analysis", audit_node("codebase_analysis", make_codebase_analysis(ctx)))
    def record_course_choice(state):
        mode = state.get("course_mode")
        if mode == "interactive":
            decision = "course_plan"
        elif mode == "guide" or not state.get("await_course_choice", False):
            decision = "course_guide"
        else:
            decision = END
        return audit_decision(
            state, decision, f"course_mode={mode or 'awaiting_user_choice'}", node="course_choice"
        )

    graph.add_node("course_choice", audit_node("course_choice", record_course_choice))
    graph.add_node("course_plan", audit_node("course_plan", make_course_plan(ctx)))
    graph.add_node("course_guide", audit_node("course_guide", make_course_guide(ctx)))
    graph.add_node("readme_sync", audit_node("readme_sync", make_readme_sync(ctx)))
    graph.add_node("readme_finalize", audit_node("readme_finalize", make_readme_finalize()))
    graph.add_node("diagrams", audit_node("diagrams", make_diagrams(ctx)))
    graph.add_node("open_pr", audit_node("open_pr", make_open_pr(ctx)))

    def route_at_start(state) -> str:
        if state.get("readme_draft"):
            return "course_choice"
        if state.get("assessment_complete") or all(
            key in state for key in ("gap_report", "readme_rating_v2", "code_understanding")
        ):
            return "readme_sync"
        return "readme_audit"

    graph.add_conditional_edges(
        START,
        route_at_start,
        {
            "readme_audit": "readme_audit",
            "readme_sync": "readme_sync",
            "course_choice": "course_choice",
        },
    )
    graph.add_edge("readme_audit", "codebase_analysis")
    graph.add_edge("codebase_analysis", "readme_sync")
    graph.add_edge("readme_sync", "course_choice")
    graph.add_conditional_edges(
        "course_choice",
        lambda state: (
            "course_plan"
            if state.get("course_mode") == "interactive"
            else "course_guide"
            if state.get("course_mode") == "guide" or not state.get("await_course_choice", False)
            else END
        ),
        {"course_plan": "course_plan", "course_guide": "course_guide", END: END},
    )
    graph.add_edge("course_plan", "readme_finalize")
    graph.add_edge("course_guide", "readme_finalize")
    graph.add_edge("readme_finalize", "diagrams")

    # conditional edge: only open a PR when pr.mode is fork or direct
    def route_after_diagrams(state) -> str:
        mode = pr_mode(settings)
        decision = "open_pr" if mode in ("fork", "direct") else END
        audit_decision(state, decision, f"pr.mode={mode}")
        return decision

    graph.add_conditional_edges("diagrams", route_after_diagrams, {"open_pr": "open_pr", END: END})
    graph.add_edge("open_pr", END)
    return graph.compile()
