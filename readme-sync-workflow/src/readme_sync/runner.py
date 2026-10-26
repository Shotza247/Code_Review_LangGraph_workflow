from collections.abc import Iterator

from .graph import build_graph

NODE_LABELS = {
    "readme_audit": "Auditing the existing README",
    "codebase_analysis": "Reviewing code, reproducibility, and architecture",
    "course_plan": "Drafting the course plan",
    "readme_sync": "Writing the synchronized README",
    "diagrams": "Generating and validating Mermaid diagrams",
    "open_pr": "Opening the pull request",
}


def stream_run(settings: dict, repo_url: str, llm=None, gh=None) -> Iterator[tuple[str, dict]]:
    """Yield (finished_node, accumulated_state) after each node completes."""
    app = build_graph(settings, llm=llm, gh=gh)
    state: dict = {"repo_url": repo_url}
    for chunk in app.stream(state, stream_mode="updates"):
        for node, update in chunk.items():
            state.update(update or {})
            yield node, dict(state)
