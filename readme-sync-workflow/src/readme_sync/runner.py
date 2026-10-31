from collections.abc import Iterator

from .graph import build_graph

NODE_LABELS = {
    "readme_audit": "Auditing the existing README",
    "codebase_analysis": "Reviewing code, reproducibility, and architecture",
    "course_choice": "Recording course format decision",
    "course_plan": "Creating the interactive course",
    "course_guide": "Creating the step-by-step study plan",
    "readme_sync": "Drafting the improved README",
    "readme_finalize": "Linking and validating the learning artifact",
    "diagrams": "Generating and validating Mermaid diagrams",
    "open_pr": "Opening the pull request",
}


def stream_run(
    settings: dict,
    repo_url: str,
    llm=None,
    gh=None,
    initial_state: dict | None = None,
) -> Iterator[tuple[str, dict]]:
    """Yield (finished_node, accumulated_state) after each node completes."""
    app = build_graph(settings, llm=llm, gh=gh)
    state: dict = dict(initial_state) if initial_state is not None else {"repo_url": repo_url}
    for chunk in app.stream(state, stream_mode="updates"):
        for node, update in chunk.items():
            state.update(update or {})
            yield node, dict(state)
