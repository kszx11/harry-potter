from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv() -> None:
        return None


@dataclass
class Config:
    api_key: str | None
    text_model: str
    typewriter_delay: float
    reduced_motion: bool
    root_dir: Path

    @property
    def save_file(self) -> Path:
        return self.root_dir / "savegame.json"

    @property
    def autosave_file(self) -> Path:
        return self.root_dir / "autosave.json"

    @classmethod
    def load(cls) -> "Config":
        load_dotenv()
        root_dir = Path(__file__).resolve().parents[2]
        reduced = os.getenv("REDUCED_MOTION", "false").strip().lower() in {"1", "true", "yes", "on"}
        return cls(
            api_key=os.getenv("OPENAI_API_KEY"),
            text_model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini"),
            typewriter_delay=float(os.getenv("TYPEWRITER_DELAY", "0.004")),
            reduced_motion=reduced,
            root_dir=root_dir,
        )
