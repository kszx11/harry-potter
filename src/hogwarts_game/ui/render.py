from __future__ import annotations

import textwrap
import time

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    RICH_AVAILABLE = True
except ModuleNotFoundError:
    Console = None
    Panel = None
    Table = None
    RICH_AVAILABLE = False

from hogwarts_game.config import Config
from hogwarts_game.domain.models import AreaProfile, GameState, LocationProfile, Mission, NpcState, Rumor
from hogwarts_game.ui import theme


TIME_MARKERS = [
    "first light over the towers",
    "breakfast in the castle",
    "late-morning corridor traffic",
    "afternoon lessons and drifting owls",
    "dinner in the Great Hall",
    "torchlit evening",
    "after-curfew hush",
]


class Renderer:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.console = Console() if RICH_AVAILABLE else None

    def title(self, text: str) -> None:
        if not RICH_AVAILABLE:
            print(f"\n=== Hogwarts :: {text} ===\n")
            return
        self.console.print(Panel.fit(text, border_style=theme.TITLE, title="Hogwarts"))

    def intro(self) -> None:
        body = (
            "You move through the wizarding world as Harry Potter: noticed whether you want it or not, "
            "surrounded by old rooms, stranger rumors, and the ordinary pressure of school life lived beside magic. "
            "Attention, timing, and who overhears you still matter."
        )
        if not RICH_AVAILABLE:
            print(body + "\n")
            return
        self.console.print(Panel(body, title="Before The Bell", border_style=theme.TITLE))

    def narrate(self, text: str) -> None:
        self._stream(textwrap.fill(text, width=92), theme.NARRATION)

    def npc(self, npc_name: str, text: str) -> None:
        if not RICH_AVAILABLE:
            print(f"{npc_name}: {textwrap.fill(text, width=88)}")
            return
        self.console.print(f"[{theme.NPC}]{npc_name}[/{theme.NPC}]: {textwrap.fill(text, width=88)}")

    def system(self, text: str) -> None:
        if not RICH_AVAILABLE:
            print(text)
            return
        self.console.print(f"[{theme.SYSTEM}]{text}[/{theme.SYSTEM}]")

    def error(self, text: str) -> None:
        if not RICH_AVAILABLE:
            print(f"ERROR: {text}")
            return
        self.console.print(f"[{theme.ERROR}]{text}[/{theme.ERROR}]")

    def meta(self, text: str) -> None:
        if not RICH_AVAILABLE:
            print(text)
            return
        self.console.print(f"[{theme.META}]{text}[/{theme.META}]")

    def location_card(
        self,
        state: GameState,
        location: LocationProfile,
        area: AreaProfile | None,
        npcs: list[NpcState],
        exit_names: list[str],
        rumors: list[Rumor],
        missions: list[Mission],
    ) -> None:
        if not RICH_AVAILABLE:
            print(f"\n[{location.name}]")
            if area is not None:
                print(f"Area: {area.name}")
            print(f"Region: {location.region}")
            print(f"Hour: {TIME_MARKERS[state.time_index % len(TIME_MARKERS)]}")
            print(f"People: {', '.join(npc.name for npc in npcs[:4]) or 'No one close enough to matter'}")
            print(f"Nearby: {', '.join(exit_names[:5]) or 'No clear route'}")
            return
        table = Table(show_header=False, box=None, pad_edge=False)
        table.add_row("Location", location.name)
        if area is not None:
            table.add_row("Area", area.name)
        table.add_row("Region", location.region)
        table.add_row("Hour", TIME_MARKERS[state.time_index % len(TIME_MARKERS)])
        table.add_row("People", ", ".join(npc.name for npc in npcs[:4]) or "No one close enough to matter")
        table.add_row("Nearby", ", ".join(exit_names[:5]) or "No clear route")
        if rumors:
            table.add_row("Rumors", f"{len([r for r in rumors if r.discovered and not r.resolved])} pressing")
        if missions:
            active = [mission for mission in missions if mission.status == "active"]
            table.add_row("Threads", f"{len(active)} active")
        self.console.print(Panel(table, title=location.name, border_style=theme.SYSTEM))

    def show_status(
        self,
        state: GameState,
        trust_hint: str,
        suggestions: list[str],
    ) -> None:
        if not RICH_AVAILABLE:
            print(
                f"Player: {state.player_name}, {state.player_title} | Pressure: {trust_hint} | "
                f"Known places: {len(state.discovered_locations)} | Known people: {len(state.known_people)}"
            )
            if suggestions:
                print(f"Suggestions: {' | '.join(suggestions[:2])}")
            return
        table = Table(show_header=False, box=None, pad_edge=False)
        table.add_row("Player", f"{state.player_name}, {state.player_title}")
        table.add_row("Present Pressure", trust_hint)
        table.add_row("Known Places", str(len(state.discovered_locations)))
        table.add_row("Known People", str(len(state.known_people)))
        if suggestions:
            table.add_row("Suggestions", suggestions[0])
            for extra in suggestions[1:2]:
                table.add_row("", extra)
        self.console.print(Panel(table, title="Present State", border_style=theme.ACCENT))

    def show_options(self, title: str, lines: list[str]) -> None:
        if not RICH_AVAILABLE:
            print(f"\n{title}")
            for line in lines:
                print(f"- {line}")
            return
        self.console.print(Panel("\n".join(lines), title=title, border_style=theme.SYSTEM))

    def divider(self) -> None:
        if not RICH_AVAILABLE:
            print("-" * 40)
            return
        self.console.rule(style=theme.ACCENT)

    def _stream(self, text: str, style: str) -> None:
        if not RICH_AVAILABLE:
            print(text)
            return
        if self.config.reduced_motion or self.config.typewriter_delay <= 0:
            self.console.print(f"[{style}]{text}[/{style}]")
            return
        for paragraph in text.split("\n"):
            self.console.print(f"[{style}]{paragraph}[/{style}]")
            time.sleep(self.config.typewriter_delay)
