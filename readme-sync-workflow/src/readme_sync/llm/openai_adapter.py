from .base import LLMAdapter

REASONING_PREFIXES = ("gpt-5", "o1", "o3", "o4")


class OpenAIAdapter(LLMAdapter):
    def __init__(self, model: str, max_tokens: int = 3000, temperature: float = 0.2, api_key: str | None = None):
        from openai import OpenAI

        self.model, self.max_tokens, self.temperature = model, max_tokens, temperature
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()  # falls back to OPENAI_API_KEY

    def _complete(self, prompt: str, system: str | None) -> str:
        messages = ([{"role": "system", "content": system}] if system else []) + [
            {"role": "user", "content": prompt}
        ]
        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_completion_tokens": self.max_tokens,
        }
        # reasoning models only accept the default temperature
        if not self.model.lower().startswith(REASONING_PREFIXES):
            kwargs["temperature"] = self.temperature
        out = self.client.chat.completions.create(**kwargs)
        return out.choices[0].message.content or ""