from __future__ import annotations

from hogwarts_game.domain.models import ParsedCommand


def parse_command(raw: str) -> ParsedCommand:
    text = raw.strip()
    lowered = text.lower()

    if not text:
        return ParsedCommand(kind="empty", raw=raw)
    if lowered in {"quit", "exit"}:
        return ParsedCommand(kind="quit", raw=raw)
    if lowered in {"menu", "main menu"}:
        return ParsedCommand(kind="menu", raw=raw)
    if lowered in {"help", "?"}:
        return ParsedCommand(kind="help", raw=raw)
    if lowered in {"hint", "suggest", "suggestions"}:
        return ParsedCommand(kind="hint", raw=raw)
    if lowered in {"areas", "area"}:
        return ParsedCommand(kind="areas", raw=raw)
    if lowered == "leave":
        return ParsedCommand(kind="leave", raw=raw)
    if lowered == "look":
        return ParsedCommand(kind="look", raw=raw)
    if lowered in {"listen", "listen closely"}:
        return ParsedCommand(kind="listen", raw=raw)
    if lowered == "people":
        return ParsedCommand(kind="people", raw=raw)
    if lowered == "where":
        return ParsedCommand(kind="where", raw=raw)
    if lowered == "map":
        return ParsedCommand(kind="map", raw=raw)
    if lowered in {"rumors", "rumours"}:
        return ParsedCommand(kind="rumors", raw=raw)
    if lowered == "journal":
        return ParsedCommand(kind="journal", raw=raw)
    if lowered == "save":
        return ParsedCommand(kind="save", raw=raw)
    if lowered == "load":
        return ParsedCommand(kind="load", raw=raw)

    for prefix in ("move to ", "move "):
        if lowered.startswith(prefix):
            return ParsedCommand(kind="move", raw=raw, target=text[len(prefix) :].strip())
    for prefix in ("go to ", "go "):
        if lowered.startswith(prefix):
            return ParsedCommand(kind="go_area", raw=raw, target=text[len(prefix) :].strip())
    if lowered.startswith("travel "):
        return ParsedCommand(kind="travel", raw=raw, target=text[7:].strip())
    if lowered.startswith("enter "):
        return ParsedCommand(kind="enter", raw=raw, target=text[6:].strip())
    for prefix in ("inspect ", "examine ", "look at "):
        if lowered.startswith(prefix):
            return ParsedCommand(kind="inspect", raw=raw, target=text[len(prefix) :].strip())
    for prefix in ("talk to ", "talk ", "speak with ", "speak to "):
        if lowered.startswith(prefix):
            return ParsedCommand(kind="talk", raw=raw, target=text[len(prefix) :].strip())
    if lowered.startswith("ask "):
        rest = text[4:].strip()
        split = rest.lower().split(" about ", maxsplit=1)
        if len(split) == 2:
            name = rest[: rest.lower().index(" about ")].strip()
            topic = rest[rest.lower().index(" about ") + 7 :].strip()
            return ParsedCommand(kind="ask", raw=raw, target=name, topic=topic)

    return ParsedCommand(kind="unknown", raw=raw, target=text)
