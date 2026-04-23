from __future__ import annotations

import json
from pathlib import Path

from hogwarts_game.domain.models import GameState


def save_state(path: Path, state: GameState) -> None:
    path.write_text(json.dumps(state.to_dict(), indent=2))


def load_state(path: Path) -> GameState:
    return GameState.from_dict(json.loads(path.read_text()))
