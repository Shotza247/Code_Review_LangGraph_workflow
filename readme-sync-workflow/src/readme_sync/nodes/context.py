from dataclasses import dataclass

from ..llm.base import LLMAdapter


@dataclass
class Context:
    """Everything a node needs besides state. Nodes are built as closures over this."""

    settings: dict
    llm: LLMAdapter
    gh: object  # GitHubClient (or a fake in tests)
    rubric: dict
