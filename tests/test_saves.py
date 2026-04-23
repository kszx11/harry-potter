from hogwarts_game.domain.models import GameState
from hogwarts_game.engine.saves import load_state, save_state


def test_save_roundtrip(tmp_path) -> None:
    path = tmp_path / "savegame.json"
    state = GameState(
        player_name="Harry Potter",
        player_title="Student Wizard",
        location_id="hogwarts_entrance_hall",
        time_index=1,
        inventory=["wand"],
    )
    save_state(path, state)
    loaded = load_state(path)
    assert loaded.player_name == "Harry Potter"
    assert loaded.location_id == "hogwarts_entrance_hall"
