import json

from langchain_core.runnables import RunnableLambda

from .prompts import SYSTEM, render


def compact_json(value, max_items: int = 2, max_string: int = 120) -> str:
    def compact(item):
        if isinstance(item, dict):
            return {key: compact(child) for key, child in item.items()}
        if isinstance(item, list):
            return [compact(child) for child in item[:max_items]]
        if isinstance(item, str):
            return item[:max_string]
        return item

    return json.dumps(compact(value), separators=(",", ":"), ensure_ascii=False)


def generate_prompt(llm, name: str, **values: str) -> str:
    """Render a named prompt and invoke the model as a small LCEL chain."""
    chain = RunnableLambda(lambda inputs: render(name, **inputs)) | RunnableLambda(
        lambda prompt: llm.generate(prompt, system=SYSTEM)
    )
    return chain.invoke(values)


def invoke_prompt(llm, prompt: str) -> str:
    """Invoke an already-rendered prompt through the shared LCEL model step."""
    chain = RunnableLambda(lambda value: llm.generate(value, system=SYSTEM))
    return chain.invoke(prompt)
