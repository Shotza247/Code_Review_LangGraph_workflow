from langgraph.graph import END, START, StateGraph

from .config import load_rubric, pr_mode
from .github.client import GitHubClient
from .llm.factory import build_llm
from .nodes.codebase_analysis import make_codebase_analysis
from .nodes.context import Context
from .nodes.course_plan import make_course_plan
from .nodes.diagrams import make_diagrams
from .nodes.open_pr import make_open_pr
from .nodes.readme_audit import make_readme_audit
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
    graph.add_node("course_plan", audit_node("course_plan", make_course_plan(ctx)))
    graph.add_node("readme_sync", audit_node("readme_sync", make_readme_sync(ctx)))
    graph.add_node("diagrams", audit_node("diagrams", make_diagrams(ctx)))
    graph.add_node("open_pr", audit_node("open_pr", make_open_pr(ctx)))

    graph.add_edge(START, "readme_audit")
    graph.add_edge("readme_audit", "codebase_analysis")
    graph.add_edge("codebase_analysis", "course_plan")
    graph.add_edge("course_plan", "readme_sync")
    graph.add_edge("readme_sync", "diagrams")

    # conditional edge: only open a PR when pr.mode is fork or direct
    def route_after_diagrams(state) -> str:
        mode = pr_mode(settings)
        decision = "open_pr" if mode in ("fork", "direct") else END
        audit_decision(state, decision, f"pr.mode={mode}")
        return decision

    graph.add_conditional_edges("diagrams", route_after_diagrams, {"open_pr": "open_pr", END: END})
    graph.add_edge("open_pr", END)
    return graph.compile()
