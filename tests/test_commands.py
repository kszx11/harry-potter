from hogwarts_game.engine.commands import parse_command


def test_parse_ask_command() -> None:
    parsed = parse_command("ask Hermione about secret passages")
    assert parsed.kind == "ask"
    assert parsed.target == "Hermione"
    assert parsed.topic == "secret passages"


def test_parse_move_command() -> None:
    parsed = parse_command("move library")
    assert parsed.kind == "move"
    assert parsed.target == "library"


def test_parse_menu_command() -> None:
    parsed = parse_command("menu")
    assert parsed.kind == "menu"


def test_parse_hint_command() -> None:
    parsed = parse_command("hint")
    assert parsed.kind == "hint"


def test_parse_go_area_command() -> None:
    parsed = parse_command("go common room hearth")
    assert parsed.kind == "go_area"
    assert parsed.target == "common room hearth"


def test_parse_enter_command() -> None:
    parsed = parse_command("enter Honeydukes")
    assert parsed.kind == "enter"


def test_parse_leave_command() -> None:
    parsed = parse_command("leave")
    assert parsed.kind == "leave"
