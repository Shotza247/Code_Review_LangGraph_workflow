from .base import LLMAdapter


def build_llm(settings: dict, api_key: str | None = None) -> LLMAdapter:
    provider = settings["llm"]["provider"]
    cfg = dict(settings["llm"].get(provider, {}))
    if provider == "huggingface":
        from .huggingface import HuggingFaceAdapter

        return HuggingFaceAdapter(**cfg, api_key=api_key)
    if provider == "openai":
        from .openai_adapter import OpenAIAdapter

        return OpenAIAdapter(**cfg, api_key=api_key)
    raise ValueError(f"Unknown llm.provider '{provider}'. Use 'huggingface' or 'openai'.")
