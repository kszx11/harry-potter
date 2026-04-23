from hogwarts_game.ai.client import OpenAIClient
from hogwarts_game.ai.world_ai import WorldAI
from hogwarts_game.config import Config
from hogwarts_game.domain.models import LocationProfile


def test_fallback_region_generation_returns_multi_location_region(tmp_path) -> None:
    config = Config(api_key=None, text_model="gpt-4.1-mini", typewriter_delay=0.0, reduced_motion=True, root_dir=tmp_path)
    ai = WorldAI(OpenAIClient(config))
    frontier = LocationProfile(
        id="forbidden_forest_edge",
        name="Forbidden Forest Edge",
        region="Forbidden Forest",
        kind="forest",
        summary="The forest begins where the school stops pretending it understands everything nearby.",
        atmosphere=["shadowed"],
    )
    region = ai.generate_region(frontier, "north annex")
    assert len(region["locations"]) == 3
    assert len(region["npcs"]) == 2
