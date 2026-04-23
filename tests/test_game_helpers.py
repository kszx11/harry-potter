from hogwarts_game.config import Config
from hogwarts_game.domain.lore import LoreCatalog
from hogwarts_game.domain.models import NpcState
from hogwarts_game.engine.game import GameApp


def test_first_talkable_npc_prefers_people_without_memory() -> None:
    talked_to = NpcState(
        name="Hermione Granger",
        title="Student",
        faction="Gryffindor",
        summary="Already spoken with.",
        speech_style=["precise"],
        traits=["smart"],
        home_location="library",
        current_location="library",
        memory=[{"speaker": "Harry", "text": "Hi"}],
    )
    new_person = NpcState(
        name="Madam Pince",
        title="Librarian",
        faction="Hogwarts Staff",
        summary="Has not been spoken with yet.",
        speech_style=["sharp"],
        traits=["watchful"],
        home_location="library",
        current_location="library",
    )

    talkable = GameApp._first_talkable_npc([talked_to, new_person])
    assert talkable is not None
    assert talkable.name == "Madam Pince"


def test_normalize_npc_reply_strips_duplicate_name_prefix() -> None:
    reply = GameApp._normalize_npc_reply("Hermione Granger", "Hermione Granger: You should check the library.")
    assert reply == "You should check the library."


def test_find_npc_allows_small_visible_name_misspelling() -> None:
    lore = LoreCatalog(player=None, locations={}, areas={}, npcs={}, rumors=[], shops={})  # type: ignore[arg-type]
    nearby = NpcState(
        name="Nell Rowan",
        title="Student",
        faction="Students",
        summary="Nearby in the hall.",
        speech_style=["plain"],
        traits=["watchful"],
        home_location="great_hall",
        current_location="great_hall",
    )

    match = lore.find_npc("Neil", {"Nell Rowan": nearby}, location_id="great_hall", area_id="")
    assert match is not None
    assert match.name == "Nell Rowan"


def test_go_accepts_nearby_location_name(tmp_path) -> None:
    app = GameApp(
        Config(
            api_key=None,
            text_model="gpt-4.1-mini",
            typewriter_delay=0.0,
            reduced_motion=True,
            root_dir=tmp_path,
        )
    )
    app.state = app._new_game()

    app._go_area("great hall")

    assert app.state is not None
    assert app.state.location_id == "great_hall"
