import re
import time
from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    """The only LLM interface nodes know about. Add a provider = add one subclass."""

    max_retries = 3

    @abstractmethod
    def _complete(self, prompt: str, system: str | None) -> str: ...

    def generate(self, prompt: str, system: str | None = None) -> str:
        last: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                text = self._complete(prompt, system)
                # strip reasoning blocks some models emit
                return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
            except Exception as exc:
                last = exc
                status = getattr(exc, "status_code", None)
                if status in (400, 401, 403, 404):  # won't fix itself on retry
                    raise RuntimeError(f"LLM call failed (HTTP {status}): {exc}") from exc
                time.sleep(2**attempt)
        raise RuntimeError(f"LLM call failed after {self.max_retries} attempts: {last}") from last
