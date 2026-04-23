from __future__ import annotations

from random import choice
from typing import Iterable

try:
    from rich.prompt import IntPrompt, Prompt
except ModuleNotFoundError:
    class Prompt:
        @staticmethod
        def ask(message: str) -> str:
            return input(f"{message}: ")

    class IntPrompt:
        @staticmethod
        def ask(message: str, default: int = 1) -> int:
            raw = input(f"{message} ")
            if not raw.strip():
                return default
            try:
                return int(raw.strip())
            except ValueError:
                return default

from hogwarts_game.ai.client import OpenAIClient
from hogwarts_game.ai.world_ai import WorldAI
from hogwarts_game.config import Config
from hogwarts_game.domain.lore import LoreCatalog
from hogwarts_game.domain.models import AreaProfile, GameState, LocationProfile, Mission, NpcState, ParsedCommand, Rumor, ShopProfile
from hogwarts_game.engine.commands import parse_command
from hogwarts_game.engine.saves import load_state, save_state
from hogwarts_game.ui.render import Renderer, TIME_MARKERS


class GameApp:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.lore = LoreCatalog.load()
        self.renderer = Renderer(config)
        self.ai = WorldAI(OpenAIClient(config))
        self.state: GameState | None = None

    def run(self) -> None:
        self.renderer.title("harry-potter")
        self.renderer.meta("Exploration-first Hogwarts and wizarding-world wandering from Harry's viewpoint.")
        self.renderer.intro()
        if not self.ai.enabled:
            self.renderer.system("OPENAI_API_KEY is not set. Fallback narration and local region generation are active.")

        while True:
            choice_value = self._startup_menu()
            if choice_value == "quit":
                return
            if choice_value == "new":
                self.state = self._new_game()
                self._render_scene(opening=True)
            else:
                path = self.config.autosave_file if choice_value == "resume" else self.config.save_file
                self.state = load_state(path)
                self.renderer.system(f"Loaded {path.name}.")
                self._render_scene(opening=True)

            assert self.state is not None
            while True:
                raw = Prompt.ask(f"[bold yellow]{self._prompt_name()}[/bold yellow]").strip()
                command = parse_command(raw)
                if command.kind == "empty":
                    continue
                outcome = self.handle_command(command)
                if outcome == "menu":
                    self.state = None
                    break
                if outcome == "quit":
                    return

    def _startup_menu(self) -> str:
        options: list[tuple[str, str]] = [("New game", "new")]
        if self.config.autosave_file.exists():
            options.append(("Resume autosave", "resume"))
        if self.config.save_file.exists():
            options.append(("Load savegame", "load"))
        options.append(("Quit", "quit"))
        prompt = "  ".join(f"{idx + 1}) {label}" for idx, (label, _) in enumerate(options))
        selected = IntPrompt.ask(prompt, default=1)
        return options[max(0, min(selected - 1, len(options) - 1))][1]

    def _new_game(self) -> GameState:
        return GameState(
            player_name=self.lore.player.name,
            player_title=self.lore.player.title,
            location_id="hogwarts_entrance_hall",
            area_id="",
            time_index=1,
            inventory=self.lore.player.starting_inventory[:],
            discovered_locations=["hogwarts_entrance_hall"],
            discovered_areas=[],
            visited_locations=["hogwarts_entrance_hall"],
            known_people=["Hermione Granger"],
            heard_rumor_ids=[],
            journal=["You step into Hogwarts ready to follow corridors, rumors, and whatever the castle chooses to reveal next."],
            facts=["Magic rarely announces its most interesting details first."],
            faction_trust={"Gryffindor": 1, "Hogwarts Staff": 0, "Students": 0, "Hogsmeade": 0, "Ministry": -1},
            npc_states={name: npc.to_dict() for name, npc in self.lore.npcs.items()},
            rumors=[rumor.to_dict() for rumor in self.lore.rumors],
            missions=[],
            dynamic_locations={},
            dynamic_shops={},
            last_narration="",
        )

    def handle_command(self, command: ParsedCommand) -> str:
        assert self.state is not None
        if command.kind == "quit":
            save_state(self.config.autosave_file, self.state)
            self.renderer.system("The castle keeps its own memory of where you've been.")
            return "quit"
        if command.kind == "menu":
            save_state(self.config.autosave_file, self.state)
            self.renderer.system("You return to the main menu. Your present route remains in autosave.")
            return "menu"
        if command.kind == "help":
            self._show_help()
            return "continue"
        if command.kind == "hint":
            self._show_hint()
            return "continue"
        if command.kind == "areas":
            self._show_areas()
            return "continue"
        if command.kind == "look":
            self._render_scene()
            return "continue"
        if command.kind == "listen":
            self._listen()
            return "continue"
        if command.kind == "people":
            self._show_people()
            return "continue"
        if command.kind == "where":
            area = self.current_area()
            place = self.current_location().name if area is None else f"{self.current_location().name} / {area.name}"
            self.renderer.system(f"{place} | {TIME_MARKERS[self.state.time_index % len(TIME_MARKERS)]}")
            return "continue"
        if command.kind == "map":
            self._show_map()
            return "continue"
        if command.kind == "rumors":
            self._show_rumors()
            return "continue"
        if command.kind == "journal":
            self._show_journal()
            return "continue"
        if command.kind == "save":
            save_state(self.config.save_file, self.state)
            self.renderer.system(f"Saved to {self.config.save_file.name}.")
            return "continue"
        if command.kind == "load":
            if self.config.save_file.exists():
                self.state = load_state(self.config.save_file)
                self.renderer.system(f"Loaded {self.config.save_file.name}.")
                self._render_scene(opening=True)
            else:
                self.renderer.error("No savegame exists yet.")
            return "continue"
        if command.kind == "inspect":
            self._inspect(command.target or "")
            return "continue"
        if command.kind == "move":
            self._move(command.target or "")
            return "continue"
        if command.kind == "go_area":
            self._go_area(command.target or "")
            return "continue"
        if command.kind == "enter":
            self._enter_shop(command.target or "")
            return "continue"
        if command.kind == "leave":
            self._leave_area()
            return "continue"
        if command.kind == "travel":
            self._travel(command.target or "")
            return "continue"
        if command.kind == "talk":
            self._talk(command.target or "")
            return "continue"
        if command.kind == "ask":
            self._ask(command.target or "", command.topic or "")
            return "continue"
        self._freeform(command.raw)
        return "continue"

    def current_location(self) -> LocationProfile:
        assert self.state is not None
        return self.all_locations()[self.state.location_id]

    def current_area(self) -> AreaProfile | None:
        assert self.state is not None
        if not self.state.area_id:
            return None
        return self.all_areas().get(self.state.area_id)

    def all_locations(self) -> dict[str, LocationProfile]:
        assert self.state is not None
        dynamic = {
            key: LocationProfile.from_dict(value)
            for key, value in self.state.dynamic_locations.items()
        }
        return {**self.lore.locations, **dynamic}

    def all_areas(self) -> dict[str, AreaProfile]:
        return self.lore.areas

    def all_shops(self) -> dict[str, ShopProfile]:
        assert self.state is not None
        dynamic = {key: ShopProfile.from_dict(value) for key, value in self.state.dynamic_shops.items()}
        return {**self.lore.shops, **dynamic}

    def npc_states(self) -> dict[str, NpcState]:
        assert self.state is not None
        return {name: NpcState.from_dict(data) for name, data in self.state.npc_states.items()}

    def rumors(self) -> list[Rumor]:
        assert self.state is not None
        return [Rumor.from_dict(item) for item in self.state.rumors]

    def missions(self) -> list[Mission]:
        assert self.state is not None
        return [Mission.from_dict(item) for item in self.state.missions]

    def _commit_npc_states(self, npc_states: dict[str, NpcState]) -> None:
        assert self.state is not None
        self.state.npc_states = {name: npc.to_dict() for name, npc in npc_states.items()}

    def _commit_rumors(self, rumors: list[Rumor]) -> None:
        assert self.state is not None
        self.state.rumors = [rumor.to_dict() for rumor in rumors]

    def _commit_missions(self, missions: list[Mission]) -> None:
        assert self.state is not None
        self.state.missions = [mission.to_dict() for mission in missions]

    def _render_scene(self, *, opening: bool = False) -> None:
        assert self.state is not None
        location = self.current_location()
        area = self.current_area()
        if area is not None:
            self._ensure_area_population(location, area)
        else:
            self._ensure_local_population(location)
        npcs = self.present_npcs(location.id, area.id if area is not None else "")
        rumors = [rumor for rumor in self.rumors() if rumor.location_id == location.id and rumor.discovered]
        shops = self.present_shops(location, area.id if area is not None else "")
        missions = [mission for mission in self.missions() if mission.status == "active"]
        exit_names = self._scene_exit_names(location, area)
        self._refresh_suggestions()
        if opening or not self.state.last_narration:
            if area is not None:
                description = self.ai.describe_area(location, area, npcs, shops, rumors, missions)
            else:
                description = self.ai.describe_location(location, npcs, shops, rumors, missions)
            self.state.last_narration = description
        else:
            description = self.state.last_narration
        self.renderer.location_card(self.state, location, area, npcs, exit_names, rumors, missions)
        self.renderer.show_status(self.state, self._trust_hint(), self.state.suggestions)
        self.renderer.narrate(description)
        save_state(self.config.autosave_file, self.state)

    def _trust_hint(self) -> str:
        assert self.state is not None
        levels = list(self.state.faction_trust.values()) or [0]
        avg = sum(levels) / len(levels)
        if avg <= -1:
            return "The people around you seem guarded, watchful, and harder to approach."
        if avg < 1:
            return "Nothing here is settled; every word still seems weighed."
        return "Some rooms and people feel a little less closed than before."

    def present_npcs(self, location_id: str, area_id: str = "") -> list[NpcState]:
        npcs = [
            npc for npc in self.npc_states().values()
            if npc.current_location == location_id and npc.current_area == area_id
        ]
        return sorted(npcs, key=lambda npc: (not npc.canonical, npc.name))

    def present_shops(self, location: LocationProfile, area_id: str = "") -> list[ShopProfile]:
        shops = self.all_shops()
        if area_id:
            return [
                shop for shop in shops.values()
                if shop.location_id == location.id and (shop.area_id == area_id or shop.interior_area_id == area_id)
            ]
        return [shops[shop_id] for shop_id in location.shop_ids if shop_id in shops]

    def _show_help(self) -> None:
        self.renderer.show_options(
            "Commands",
            [
                "look",
                "hint",
                "areas",
                "inspect <thing>",
                "listen",
                "people",
                "talk <name>",
                "ask <name> about <topic>",
                "go <area>",
                "enter <shop>",
                "leave",
                "move <place>",
                "travel <place>",
                "where",
                "map",
                "rumors",
                "journal",
                "menu",
                "save",
                "load",
                "quit",
            ],
        )

    def _show_hint(self) -> None:
        assert self.state is not None
        self._refresh_suggestions()
        lines = self.state.suggestions[:] or ["Nothing presses strongly at the moment. Look, listen, or speak with someone nearby."]
        self.renderer.show_options("Quiet Guidance", lines)

    def _show_areas(self) -> None:
        location = self.current_location()
        current_area = self.current_area()
        areas = self.areas_for_location(location.id)
        if not areas:
            self.renderer.system("This place does not open into smaller spaces yet.")
            return
        if current_area is None:
            lines = [f"{area.name} - {area.summary}" for area in areas]
        else:
            linked = [self.all_areas()[area_id] for area_id in current_area.linked_areas if area_id in self.all_areas()]
            lines = [f"{area.name} - {area.summary}" for area in linked]
            lines.append("Use 'leave' to return to the broader location.")
        self.renderer.show_options("Internal Areas", lines)

    def _show_people(self) -> None:
        location = self.current_location()
        area = self.current_area()
        npcs = self.present_npcs(location.id, area.id if area is not None else "")
        if not npcs:
            self.renderer.system("No one near enough seems willing to engage.")
            return
        lines = []
        for npc in npcs:
            trouble = f" Trouble: {npc.troubles[0]}." if npc.troubles else ""
            lines.append(f"{npc.name}, {npc.title} [{npc.faction}] - {npc.summary}{trouble}")
        self.renderer.show_options("People Near At Hand", lines)

    def _show_map(self) -> None:
        assert self.state is not None
        location = self.current_location()
        area = self.current_area()
        all_locations = self.all_locations()
        lines = [f"Current: {location.name}"]
        if area is not None:
            lines.append(f"Inside: {area.name}")
        lines.extend(f"Road: {all_locations[loc_id].name}" for loc_id in location.linked_locations if loc_id in all_locations)
        if area is not None and area.linked_areas:
            lines.extend(
                f"Area route: {self.all_areas()[area_id].name}"
                for area_id in area.linked_areas
                if area_id in self.all_areas()
            )
        discovered = [
            all_locations[loc_id].name
            for loc_id in self.state.discovered_locations[-12:]
            if loc_id in all_locations
        ]
        lines.append(f"Known terrain: {', '.join(discovered) or 'almost nothing yet'}")
        self.renderer.show_options("Known Routes", lines)

    def _show_rumors(self) -> None:
        rumors = [rumor for rumor in self.rumors() if rumor.discovered]
        if not rumors:
            self.renderer.system("You have not yet gathered a rumor worth keeping.")
            return
        lines = []
        for rumor in rumors[-8:]:
            status = "resolved" if rumor.resolved else "alive"
            lines.append(f"[{status}] {rumor.text}")
        self.renderer.show_options("Rumors", lines)

    def _show_journal(self) -> None:
        assert self.state is not None
        missions = self.missions()
        lines: list[str] = []
        if missions:
            for mission in missions[-6:]:
                lines.append(f"{mission.title} [{mission.status}] - {mission.description}")
        if self.state.journal:
            lines.extend(self.state.journal[-6:])
        self.renderer.show_options("Journal", lines or ["No written threads yet."])

    def _listen(self) -> None:
        assert self.state is not None
        location = self.current_location()
        area = self.current_area()
        rumors = self.rumors()
        local = [rumor for rumor in rumors if rumor.location_id == location.id and not rumor.discovered]
        if local:
            heard = local[0]
            heard.discovered = True
            if heard.id not in self.state.heard_rumor_ids:
                self.state.heard_rumor_ids.append(heard.id)
            self.state.journal.append(f"Heard rumor: {heard.text}")
            self._commit_rumors(rumors)
            self._spawn_mission_from_rumor(heard)
            self._advance_time()
            self.renderer.narrate(
                f"You keep still long enough to hear what the place is trying not to say. {heard.text}"
            )
            save_state(self.config.autosave_file, self.state)
            return
        if area is not None:
            self.renderer.narrate(
                f"Inside {area.name}, the smaller sounds matter more: a portrait clearing its throat, a page turning by itself, "
                "and the pause people make when they think a room may be listening."
            )
            return
        line = choice(
            [
                "The place speaks in quieter terms: footsteps on stone, distant owls, and the hush that follows a sentence cut short.",
                "Nothing definite rises above the ordinary caution of castle life, yet the scene remains full of withheld meaning.",
            ]
        )
        self.renderer.narrate(line)

    def _inspect(self, target: str) -> None:
        assert self.state is not None
        if not target:
            self.renderer.error("Inspect what?")
            return
        location = self.current_location()
        area = self.current_area()
        lowered = target.lower()
        landmark_source = area.landmarks if area is not None else location.landmarks
        for landmark in landmark_source:
            if lowered in landmark.lower():
                scope_name = area.name if area is not None else location.name
                detail = self.ai.narrate_action(location, f"inspect {landmark} in {scope_name}")
                self.state.facts.append(f"{scope_name}: {landmark}")
                self.state.journal.append(f"Inspected {landmark} in {scope_name}.")
                self.state.last_narration = detail
                self._advance_time()
                self.renderer.narrate(detail)
                save_state(self.config.autosave_file, self.state)
                return
        shops = self.present_shops(location, area.id if area is not None else "")
        for shop in shops:
            if lowered in shop.name.lower() or lowered in shop.owner.lower():
                text = (
                    f"{shop.name} carries the look of necessity rather than luxury. {shop.flavor} "
                    f"Goods in sight include {', '.join(shop.goods[:4])}."
                )
                self.state.journal.append(f"Inspected {shop.name}.")
                self.renderer.narrate(text)
                return
        npc = self.lore.find_npc(target, self.npc_states(), location.id, area.id if area is not None else "")
        if npc is not None:
            line = (
                f"{npc.name} bears the marks of {npc.summary.lower()} The person's manner suggests "
                f"{', '.join(npc.traits[:2])}, and perhaps more caution than courtesy."
            )
            self.state.facts.append(f"{npc.name}: {npc.summary}")
            self.state.known_people = list(dict.fromkeys(self.state.known_people + [npc.name]))
            self.renderer.narrate(line)
            return
        if area is None:
            target_area = self.lore.find_area(target, self.all_areas(), location.id)
            if target_area is not None:
                self.renderer.narrate(
                    f"{target_area.name} lies within {location.name}. You could go there directly if you want a closer look."
                )
                return
        self.renderer.error("Nothing by that name stands clearly before you.")

    def _move(self, target: str) -> None:
        assert self.state is not None
        if not target:
            self.renderer.error("Move where?")
            return
        location = self.current_location()
        all_locations = self.all_locations()
        target_location = self.lore.find_location(target, {loc_id: all_locations[loc_id] for loc_id in location.linked_locations if loc_id in all_locations})
        if target_location is None:
            self.renderer.error("No such nearby route is open from here.")
            return
        self._arrive(target_location, traveled=True)

    def _go_area(self, target: str) -> None:
        assert self.state is not None
        if not target:
            self.renderer.error("Go where inside this place?")
            return
        location = self.current_location()
        all_locations = self.all_locations()
        current_area = self.current_area()
        if current_area is None:
            allowed = {area.id for area in self.areas_for_location(location.id)}
        else:
            allowed = set(current_area.linked_areas)
        area = self.lore.find_area(target, self.all_areas(), location.id, allowed)
        if area is None:
            target_location = self.lore.find_location(
                target,
                {loc_id: all_locations[loc_id] for loc_id in location.linked_locations if loc_id in all_locations},
            )
            if target_location is not None:
                self._arrive(target_location, traveled=False)
                return
            self.renderer.error("No such nearby route is open from here.")
            return
        self.state.area_id = area.id
        self.state.discovered_areas = list(dict.fromkeys(self.state.discovered_areas + [area.id]))
        self.state.journal.append(f"Entered {area.name} in {location.name}.")
        self._ensure_area_population(location, area)
        self._advance_time()
        self.state.last_narration = self.ai.describe_area(
            location,
            area,
            self.present_npcs(location.id, area.id),
            self.present_shops(location, area.id),
            [rumor for rumor in self.rumors() if rumor.location_id == location.id and rumor.discovered],
            [mission for mission in self.missions() if mission.status == "active"],
        )
        self._render_scene()

    def _enter_shop(self, target: str) -> None:
        assert self.state is not None
        if not target:
            self.renderer.error("Enter which shop?")
            return
        location = self.current_location()
        lowered = target.lower()
        shop = next(
            (
                candidate for candidate in self.all_shops().values()
                if candidate.location_id == location.id
                and (lowered in candidate.name.lower() or lowered in candidate.owner.lower())
            ),
            None,
        )
        if shop is None or not shop.interior_area_id:
            self.renderer.error("No enterable shop by that name is here.")
            return
        area = self.all_areas().get(shop.interior_area_id)
        if area is None:
            self.renderer.error("That interior is not yet fully mapped.")
            return
        self.state.area_id = area.id
        self.state.discovered_areas = list(dict.fromkeys(self.state.discovered_areas + [area.id]))
        self.state.journal.append(f"Entered {shop.name}.")
        self.state.last_narration = ""
        self._render_scene(opening=True)

    def _leave_area(self) -> None:
        assert self.state is not None
        area = self.current_area()
        if area is None:
            self.renderer.system("You are already in the broader location.")
            return
        self.state.area_id = ""
        self.state.journal.append(f"Left {area.name} for the broader scene of {self.current_location().name}.")
        self.state.last_narration = ""
        self._advance_time()
        self._render_scene(opening=True)

    def _travel(self, target: str) -> None:
        assert self.state is not None
        if not target:
            self.renderer.error("Travel where?")
            return
        all_locations = self.all_locations()
        existing = self.lore.find_location(target, all_locations)
        if existing is not None:
            self._arrive(existing, traveled=True, long_route=True)
            return
        if not self.current_location().can_expand:
            self.renderer.error("No convincing longer route suggests itself from here. Try listening for a lead first.")
            return
        self._generate_region(target)

    def _arrive(self, location: LocationProfile, *, traveled: bool, long_route: bool = False) -> None:
        assert self.state is not None
        self.state.location_id = location.id
        self.state.area_id = ""
        self.state.discovered_locations = list(dict.fromkeys(self.state.discovered_locations + [location.id]))
        self.state.visited_locations.append(location.id)
        self.state.journal.append(
            f"Reached {location.name}{' by a longer route' if long_route else ''}."
        )
        if location.resident_npcs:
            self.state.known_people = list(dict.fromkeys(self.state.known_people + location.resident_npcs[:2]))
        self._ensure_local_population(location)
        self._advance_time(amount=2 if traveled else 1)
        self._drift_npcs()
        self.state.last_narration = self.ai.describe_location(
            location,
            self.present_npcs(location.id),
            self.present_shops(location),
            [rumor for rumor in self.rumors() if rumor.location_id == location.id and rumor.discovered],
            [mission for mission in self.missions() if mission.status == "active"],
        )
        self._render_scene()

    def _talk(self, target: str) -> None:
        assert self.state is not None
        if not target:
            self.renderer.error("Talk to whom?")
            return
        npc_states = self.npc_states()
        current_area = self.current_area()
        npc = self.lore.find_npc(
            target,
            npc_states,
            self.current_location().id,
            current_area.id if current_area is not None else "",
        )
        if npc is None:
            self.renderer.error("No one by that name is presently before you.")
            return
        self.state.known_people = list(dict.fromkeys(self.state.known_people + [npc.name]))
        speaker = self.state.player_name.split()[0]
        self.renderer.system(f"You turn to {npc.name}. Type 'bye' to step away.")
        while True:
            line = Prompt.ask(speaker).strip()
            if line.lower() in {"bye", "leave", "goodbye", "back"}:
                self.renderer.system("You return your attention to the larger scene.")
                self._commit_npc_states(npc_states)
                save_state(self.config.autosave_file, self.state)
                return
            reply = self._normalize_npc_reply(npc.name, self.ai.npc_reply(npc, self.current_location(), line))
            npc.memory.append({"speaker": speaker, "text": line})
            npc.memory.append({"speaker": npc.name, "text": reply})
            npc.memory = npc.memory[-12:]
            if npc.disposition < 3:
                npc.disposition += 1
            self._maybe_create_personal_mission(npc)
            self._nudge_faction(npc.faction, 1)
            self._advance_time()
            self.renderer.npc(npc.name, reply)

    def _ask(self, target: str, topic: str) -> None:
        if not target or not topic:
            self.renderer.error("Use 'ask <name> about <topic>'.")
            return
        npc_states = self.npc_states()
        current_area = self.current_area()
        npc = self.lore.find_npc(
            target,
            npc_states,
            self.current_location().id,
            current_area.id if current_area is not None else "",
        )
        if npc is None:
            self.renderer.error("That person is not here.")
            return
        reply = self._normalize_npc_reply(
            npc.name,
            self.ai.npc_reply(npc, self.current_location(), f"Tell me about {topic}."),
        )
        npc.memory.append({"speaker": self.state.player_name.split()[0], "text": f"Asked about {topic}"})
        npc.memory.append({"speaker": npc.name, "text": reply})
        if topic.lower() in {"hogwarts", "forest", "hogsmeade", "classes", "library", "secret passages", "diagon alley"}:
            self.state.facts.append(f"{npc.name} spoke of {topic}.")
        self._commit_npc_states(npc_states)
        self._advance_time()
        self.renderer.npc(npc.name, reply)

    def _freeform(self, raw: str) -> None:
        assert self.state is not None
        line = self.ai.narrate_action(self.current_location(), raw)
        self.state.journal.append(f"Tried: {raw}")
        self.state.last_narration = line
        self._advance_time()
        self.renderer.narrate(line)

    def _spawn_mission_from_rumor(self, rumor: Rumor) -> None:
        missions = self.missions()
        if any(mission.id == f"mission_{rumor.id}" for mission in missions):
            return
        title = {
            "castle": "A Castle Thread",
            "classes": "A Classroom Problem",
            "forest": "A Forest Warning",
            "hogsmeade": "A Hogsmeade Lead",
            "diagon": "A Diagon Alley Matter",
            "secrets": "A Hidden Passage Thread",
            "ministry": "A Ministry Whisper",
            "frontier": "A Newly Opened Route",
        }.get(rumor.topic, "An Uneasy Thread")
        missions.append(
            Mission(
                id=f"mission_{rumor.id}",
                title=title,
                description=rumor.text,
                giver=rumor.source,
                location_id=rumor.location_id,
                kind="rumor",
                notes=[
                    f"Listen further in {self.all_locations()[rumor.location_id].name}.",
                    f"Seek whoever stands nearest to {rumor.person_hint or rumor.source}.",
                ],
            )
        )
        self._commit_missions(missions)

    def _maybe_create_personal_mission(self, npc: NpcState) -> None:
        assert self.state is not None
        missions = self.missions()
        mission_id = f"favor_{_slug(npc.name)}"
        if npc.troubles and not any(mission.id == mission_id for mission in missions):
            missions.append(
                Mission(
                    id=mission_id,
                    title=f"A Favor For {npc.name}",
                    description=npc.troubles[0],
                    giver=npc.name,
                    location_id=npc.current_location,
                    kind="favor",
                    notes=[f"Return to {npc.name} after learning more."],
                )
            )
            self.state.journal.append(f"{npc.name} now seems tied to a possible favor: {npc.troubles[0]}.")
            self._commit_missions(missions)

    def _generate_region(self, requested_name: str) -> None:
        assert self.state is not None
        frontier = self.current_location()
        region = self.ai.generate_region(frontier, requested_name)
        region_locations: list[LocationProfile] = []
        prior_id = frontier.id
        for raw in region["locations"]:
            loc = LocationProfile(
                id=raw["id"],
                name=raw["name"],
                region=region["region_name"],
                kind=raw["kind"],
                summary=raw["summary"],
                atmosphere=raw["atmosphere"],
                landmarks=raw["landmarks"],
                linked_locations=[prior_id],
                resident_npcs=[],
                rumor_tags=["generated", "frontier"],
                travel_keywords=raw["travel_keywords"],
                can_expand=True,
                generated=True,
            )
            if region_locations:
                region_locations[-1].linked_locations.append(loc.id)
                loc.linked_locations.append(region_locations[-1].id)
            region_locations.append(loc)
            prior_id = loc.id

        all_locations = self.all_locations()
        if region_locations:
            if region_locations[0].id not in all_locations[frontier.id].linked_locations:
                all_locations[frontier.id].linked_locations.append(region_locations[0].id)
            if frontier.id in self.lore.locations:
                self.lore.locations[frontier.id].linked_locations = all_locations[frontier.id].linked_locations

        for loc in region_locations:
            self.state.dynamic_locations[loc.id] = loc.to_dict()

        npc_states = self.npc_states()
        for idx, raw_npc in enumerate(region["npcs"]):
            anchor_location = region_locations[min(idx, len(region_locations) - 1)]
            npc = NpcState(
                name=raw_npc["name"],
                title=raw_npc["title"],
                faction=raw_npc["faction"],
                summary=raw_npc["summary"],
                speech_style=["guarded", "spare", "watchful"],
                traits=raw_npc["traits"],
                home_location=anchor_location.id,
                current_location=anchor_location.id,
                generated=True,
                troubles=raw_npc["troubles"],
                secrets=raw_npc["secrets"],
            )
            npc_states[npc.name] = npc
            anchor_location.resident_npcs.append(npc.name)
            self.state.known_people = list(dict.fromkeys(self.state.known_people + [npc.name]))
            self.state.dynamic_locations[anchor_location.id] = anchor_location.to_dict()

        rumor = Rumor(
            id=f"generated_{_slug(region['region_name'])}",
            text=region["rumor"],
            source=frontier.name,
            location_id=region_locations[0].id,
            topic="frontier",
            leads_to=region_locations[-1].id,
            discovered=True,
        )
        rumors = self.rumors()
        rumors.append(rumor)
        self._commit_rumors(rumors)
        self._commit_npc_states(npc_states)
        self.state.journal.append(f"Discovered a new region: {region['region_name']}.")
        self._spawn_mission_from_rumor(rumor)
        self._arrive(region_locations[0], traveled=True, long_route=True)

    def _advance_time(self, amount: int = 1) -> None:
        assert self.state is not None
        self.state.time_index = (self.state.time_index + amount) % len(TIME_MARKERS)

    def _nudge_faction(self, faction: str, delta: int) -> None:
        assert self.state is not None
        self.state.faction_trust[faction] = self.state.faction_trust.get(faction, 0) + delta

    def _drift_npcs(self) -> None:
        npc_states = self.npc_states()
        location = self.current_location()
        for npc in npc_states.values():
            if npc.generated and npc.current_location == npc.home_location and location.id != npc.current_location:
                continue
            if npc.shop_id:
                npc.current_location = npc.home_location
                npc.current_area = npc.home_area
            elif npc.generated and location.id in self.all_locations():
                npc.current_location = choice([npc.current_location, npc.home_location])
                npc.current_area = npc.home_area
        self._commit_npc_states(npc_states)

    def _ensure_local_population(self, location: LocationProfile) -> None:
        npc_states = self.npc_states()
        present = [
            npc for npc in npc_states.values()
            if npc.current_location == location.id and not npc.current_area
        ]
        target_count = 2 if location.kind in {"castle", "classroom", "dungeons", "village", "street"} else 1
        existing_names = list(npc_states.keys())
        created = False
        while len(present) < target_count:
            raw = self.ai.generate_local_npc(location, existing_names)
            npc = NpcState(
                name=raw["name"],
                title=raw["title"],
                faction=raw["faction"],
                summary=raw["summary"],
                speech_style=["guarded", "plain", "socially aware"],
                traits=raw["traits"],
                home_location=location.id,
                current_location=location.id,
                home_area="",
                current_area="",
                generated=True,
                troubles=raw["troubles"],
                secrets=raw["secrets"],
            )
            npc_states[npc.name] = npc
            present.append(npc)
            existing_names.append(npc.name)
            created = True
        if created:
            self._commit_npc_states(npc_states)

    def _ensure_area_population(self, location: LocationProfile, area: AreaProfile) -> None:
        npc_states = self.npc_states()
        present = [
            npc for npc in npc_states.values()
            if npc.current_location == location.id and npc.current_area == area.id
        ]
        existing_names = list(npc_states.keys())
        created = False
        while len(present) < 1:
            raw = self.ai.generate_area_npc(location, area, existing_names)
            npc = NpcState(
                name=raw["name"],
                title=raw["title"],
                faction=raw["faction"],
                summary=raw["summary"],
                speech_style=["guarded", "plain", "socially aware"],
                traits=raw["traits"],
                home_location=location.id,
                current_location=location.id,
                home_area=area.id,
                current_area=area.id,
                generated=True,
                troubles=raw["troubles"],
                secrets=raw["secrets"],
            )
            npc_states[npc.name] = npc
            present.append(npc)
            existing_names.append(npc.name)
            created = True
        if created:
            self._commit_npc_states(npc_states)

    def _refresh_suggestions(self) -> None:
        assert self.state is not None
        self.state.suggestions = self._build_suggestions()[:3]

    def _build_suggestions(self) -> list[str]:
        assert self.state is not None
        location = self.current_location()
        area = self.current_area()
        suggestions: list[str] = []
        all_locations = self.all_locations()
        all_areas = self.all_areas()
        rumors = self.rumors()
        missions = [mission for mission in self.missions() if mission.status == "active"]
        present_npcs = self.present_npcs(location.id, area.id if area is not None else "")

        local_hidden_rumors = [rumor for rumor in rumors if rumor.location_id == location.id and not rumor.discovered]
        if local_hidden_rumors:
            suggestions.append("A quiet thread: listen here before the local rumor goes cold.")

        local_mission = next((mission for mission in missions if mission.location_id == location.id), None)
        if local_mission is not None:
            suggestions.append(f"A pressure point: {local_mission.title} can be advanced here.")

        talkable = self._first_talkable_npc(present_npcs)
        if talkable is not None:
            focus = talkable.troubles[0] if talkable.troubles else "what weighs on this place"
            focus_text = focus.rstrip(".")
            if focus_text.lower().startswith("needs help"):
                focus_text = "the quiet trouble there"
            suggestions.append(f"A living thread: talk to {talkable.name} about {focus_text.lower()}.")

        if area is None:
            unexplored_area = next(
                (
                    candidate for candidate in self.areas_for_location(location.id)
                    if candidate.id not in self.state.discovered_areas
                ),
                None,
            )
            if unexplored_area is not None:
                suggestions.append(f"An inner route: go {unexplored_area.name} to examine this place more closely.")
            unexplored_exit = next(
                (all_locations[loc_id] for loc_id in location.linked_locations if loc_id in all_locations and loc_id not in self.state.discovered_locations),
                None,
            )
            if unexplored_exit is not None:
                suggestions.append(f"An open route: move {unexplored_exit.name} to widen the map.")
        else:
            unexplored_area_link = next(
                (
                    all_areas[area_id] for area_id in area.linked_areas
                    if area_id in all_areas and area_id not in self.state.discovered_areas
                ),
                None,
            )
            if unexplored_area_link is not None:
                suggestions.append(f"A close route: go {unexplored_area_link.name} while the local trail is still clear.")
            suggestions.append("A broader perspective: leave when you want the whole location back in view.")

        remote_mission = next((mission for mission in missions if mission.location_id != location.id), None)
        if remote_mission is not None:
            target_location = all_locations.get(remote_mission.location_id)
            if target_location is not None:
                suggestions.append(f"A live route: {target_location.name} holds {remote_mission.title}.")

        if location.can_expand:
            suggestions.append("A longer thread: travel toward a named place if you want the map to open farther.")

        if not suggestions and location.landmarks:
            suggestions.append(f"A close detail: inspect {location.landmarks[0]} before moving on.")

        seen: set[str] = set()
        unique: list[str] = []
        for line in suggestions:
            if line not in seen:
                unique.append(line)
                seen.add(line)
        return unique

    def _scene_exit_names(self, location: LocationProfile, area: AreaProfile | None) -> list[str]:
        if area is not None:
            exits = [self.all_areas()[area_id].name for area_id in area.linked_areas if area_id in self.all_areas()]
            exits.append("leave")
            return exits
        area_names = [area_item.name for area_item in self.areas_for_location(location.id)[:3]]
        location_names = [
            self.all_locations()[loc_id].name for loc_id in location.linked_locations if loc_id in self.all_locations()
        ]
        return area_names + location_names

    def areas_for_location(self, location_id: str) -> list[AreaProfile]:
        interior_ids = self.shop_interior_area_ids()
        return [
            area for area in self.all_areas().values()
            if area.parent_location_id == location_id and area.id not in interior_ids
        ]

    def shop_interior_area_ids(self) -> set[str]:
        return {shop.interior_area_id for shop in self.all_shops().values() if shop.interior_area_id}

    def _prompt_name(self) -> str:
        area = self.current_area()
        if area is not None:
            return area.name
        return self.current_location().name

    @staticmethod
    def _first_talkable_npc(present_npcs: list[NpcState]) -> NpcState | None:
        return next((npc for npc in present_npcs if not npc.memory), None)

    @staticmethod
    def _normalize_npc_reply(npc_name: str, reply: str) -> str:
        cleaned = reply.strip()
        lowered = cleaned.lower()
        name_lower = npc_name.lower()
        for prefix in (
            f"{name_lower}:",
            f"{name_lower} says:",
            f"{name_lower} said:",
            f"{name_lower},",
            f"{name_lower} ",
        ):
            if lowered.startswith(prefix):
                return cleaned[len(prefix):].strip()
        return cleaned


def _slug(text: str) -> str:
    clean = "".join(ch.lower() if ch.isalnum() else "_" for ch in text)
    while "__" in clean:
        clean = clean.replace("__", "_")
    return clean.strip("_")
