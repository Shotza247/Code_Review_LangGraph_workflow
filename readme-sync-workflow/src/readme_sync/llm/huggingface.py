import os

from .base import LLMAdapter


class HuggingFaceAdapter(LLMAdapter):
    def __init__(self, model: str, max_tokens: int = 3000, temperature: float = 0.2, api_key: str | None = None):
        from huggingface_hub import InferenceClient

        self.model, self.max_tokens, self.temperature = model, max_tokens, temperature
        self.client = InferenceClient(model=model, token=api_key or os.getenv("HF_TOKEN"))

    def _complete(self, prompt: str, system: str | None) -> str:
        messages = ([{"role": "system", "content": system}] if system else []) + [
            {"role": "user", "content": prompt}
        ]
        out = self.client.chat_completion(
            messages=messages, max_tokens=self.max_tokens, temperature=self.temperature
        )
        return out.choices[0].message.content or ""
