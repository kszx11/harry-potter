from __future__ import annotations

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

from hogwarts_game.config import Config


class OpenAIClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = OpenAI(api_key=config.api_key) if config.api_key and OpenAI is not None else None

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def text(self, *, instructions: str, prompt: str, temperature: float = 0.9) -> str:
        if not self.client:
            return ""
        try:
            response = self.client.chat.completions.create(
                model=self.config.text_model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": prompt},
                ],
            )
            return (response.choices[0].message.content or "").strip()
        except Exception:
            return ""
