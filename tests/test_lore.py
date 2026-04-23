from hogwarts_game.domain.lore import LoreCatalog


def test_lore_loads_core_hogwarts_content() -> None:
    lore = LoreCatalog.load()
    assert lore.player.name == "Harry Potter"
    assert "hogwarts_entrance_hall" in lore.locations
    assert "gryffindor_common_room" in lore.areas
    assert "Hermione Granger" in lore.npcs
    assert lore.rumors
