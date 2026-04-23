from __future__ import annotations

import json
from random import choice

from hogwarts_game.ai.client import OpenAIClient
from hogwarts_game.domain.models import AreaProfile, LocationProfile, Mission, NpcState, Rumor, ShopProfile


class WorldAI:
    def __init__(self, client: OpenAIClient) -> None:
        self.client = client

    @property
    def enabled(self) -> bool:
        return self.client.enabled

    def describe_location(
        self,
        location: LocationProfile,
        npcs: list[NpcState],
        shops: list[ShopProfile],
        rumors: list[Rumor],
        missions: list[Mission],
    ) -> str:
        instructions = (
            "Write like a restrained Harry Potter scene description. Stress atmosphere, castle geography, magical detail, "
            "small social tensions, routine, and overheard possibility. Avoid parody, generic fantasy, and modern slang. "
            "Keep to 4-6 sentences."
        )
        prompt = (
            f"Location: {location.name}\n"
            f"Region: {location.region}\n"
            f"Summary: {location.summary}\n"
            f"Atmosphere: {', '.join(location.atmosphere)}\n"
            f"Landmarks: {', '.join(location.landmarks)}\n"
            f"Nearby people: {', '.join(f'{npc.name} ({npc.title})' for npc in npcs) or 'none'}\n"
            f"Nearby shops: {', '.join(shop.name for shop in shops) or 'none'}\n"
            f"Heard rumors: {', '.join(r.text for r in rumors[:2]) or 'none'}\n"
            f"Active pressures: {', '.join(m.title for m in missions[:2]) or 'none'}"
        )
        text = self.client.text(instructions=instructions, prompt=prompt, temperature=0.95)
        if text:
            return text
        return self._fallback_location(location, npcs, shops, rumors, missions)

    def describe_area(
        self,
        location: LocationProfile,
        area: AreaProfile,
        npcs: list[NpcState],
        shops: list[ShopProfile],
        rumors: list[Rumor],
        missions: list[Mission],
    ) -> str:
        instructions = (
            "Write like a Harry Potter scene description for a smaller explorable area within a larger place. "
            "Keep the scale intimate, spatially precise, and magical without becoming melodramatic. Use 3-5 sentences."
        )
        prompt = (
            f"Parent location: {location.name}\n"
            f"Area: {area.name}\n"
            f"Area summary: {area.summary}\n"
            f"Atmosphere: {', '.join(area.atmosphere)}\n"
            f"Landmarks: {', '.join(area.landmarks)}\n"
            f"Nearby people: {', '.join(f'{npc.name} ({npc.title})' for npc in npcs) or 'none'}\n"
            f"Nearby shops: {', '.join(shop.name for shop in shops) or 'none'}\n"
            f"Heard rumors: {', '.join(r.text for r in rumors[:2]) or 'none'}\n"
            f"Active pressures: {', '.join(m.title for m in missions[:2]) or 'none'}"
        )
        text = self.client.text(instructions=instructions, prompt=prompt, temperature=0.95)
        if text:
            return text
        return self._fallback_area(location, area, npcs, shops, rumors, missions)

    def npc_reply(self, npc: NpcState, location: LocationProfile, player_line: str) -> str:
        instructions = (
            "You are roleplaying a Harry Potter world NPC speaking with Harry Potter. Stay in-world. "
            "Keep the line compact, observant, and characterful. Never mention being an AI."
        )
        memory = "\n".join(f"{entry['speaker']}: {entry['text']}" for entry in npc.memory[-6:])
        prompt = (
            f"NPC: {npc.name}, {npc.title}\n"
            f"Faction: {npc.faction}\n"
            f"Summary: {npc.summary}\n"
            f"Traits: {', '.join(npc.traits)}\n"
            f"Troubles: {', '.join(npc.troubles) or 'none'}\n"
            f"Secrets: {', '.join(npc.secrets) or 'none'}\n"
            f"Location: {location.name} - {location.summary}\n"
            f"Recent exchange:\n{memory or '(none)'}\n"
            f"Harry says: {player_line}"
        )
        text = self.client.text(instructions=instructions, prompt=prompt, temperature=0.98)
        if text:
            return text
        tone = choice(
            [
                "Glances past you before answering, as if portraits might be listening",
                "Lowers their voice in the practiced way of someone used to castle gossip",
                "Answers with the caution of a person who knows Hogwarts keeps more than one kind of memory",
            ]
        )
        return f"{tone}. \"{self._fallback_speech(npc, player_line)}\""

    def narrate_action(self, location: LocationProfile, action_text: str) -> str:
        instructions = (
            "Narrate the outcome of one grounded magical or social action in the Harry Potter world. "
            "Stay concise and plausible. Use 2-4 sentences."
        )
        prompt = f"Location: {location.name}\nSummary: {location.summary}\nAction: {action_text}"
        text = self.client.text(instructions=instructions, prompt=prompt, temperature=0.85)
        if text:
            return text
        return (
            f"In {location.name}, even a small action changes the attention around you. "
            "At Hogwarts and beyond, the room often seems to notice first and explain itself later."
        )

    def generate_region(self, frontier: LocationProfile, requested_name: str) -> dict:
        instructions = (
            "Create a lore-compatible magical region in the Harry Potter world. Return strict JSON with keys: "
            "region_name, summary, locations, npcs, rumor. "
            "locations is an array of 3 items with keys id, name, kind, summary, atmosphere, landmarks, travel_keywords. "
            "npcs is an array of 2 items with keys name, title, faction, summary, traits, troubles, secrets."
        )
        prompt = (
            f"Create a new magical region branching from {frontier.name}. "
            f"Requested clue or name: {requested_name}. "
            "The result should feel like a plausible extension of Hogwarts, Hogsmeade, Diagon Alley, or nearby wizarding spaces."
        )
        raw = self.client.text(instructions=instructions, prompt=prompt, temperature=1.0)
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
        slug = _slug(requested_name or "north annex")
        region_name = requested_name.title() if requested_name else "North Annex"
        return {
            "region_name": region_name,
            "summary": "A half-forgotten magical annex of side passages, working rooms, and odd corners that only become obvious once someone starts looking for them.",
            "locations": [
                {
                    "id": f"{slug}_landing",
                    "name": f"{region_name} Landing",
                    "kind": "castle",
                    "summary": "A narrow landing where the stairs pause just long enough to suggest there may once have been a busier route here.",
                    "atmosphere": ["dusty", "watchful", "half-reopened"],
                    "landmarks": ["lantern niche", "crooked stair", "brass room plaque"],
                    "travel_keywords": ["landing", "annex stairs", "plaque"],
                },
                {
                    "id": f"{slug}_workrooms",
                    "name": f"{region_name} Workrooms",
                    "kind": "classroom",
                    "summary": "A run of old workrooms filled with benches, cupboards, and the feeling that somebody tidied in a hurry years ago and never quite came back.",
                    "atmosphere": ["quiet", "curious", "practical"],
                    "landmarks": ["labeled cabinets", "folding screens", "chalk roster board"],
                    "travel_keywords": ["workrooms", "benches", "cabinets"],
                },
                {
                    "id": f"{slug}_gallery",
                    "name": f"{region_name} Gallery",
                    "kind": "castle",
                    "summary": "A long gallery of cases and windows where magical odds and ends sit arranged with more care than explanation.",
                    "atmosphere": ["strange", "still", "secretive"],
                    "landmarks": ["glass cases", "portrait recess", "moonlit windows"],
                    "travel_keywords": ["gallery", "cases", "windows"],
                },
            ],
            "npcs": [
                {
                    "name": "Cressida Vale",
                    "title": "Archive Assistant",
                    "faction": "Hogwarts Staff",
                    "summary": "A brisk witch who treats old rooms as if they were temperamental pupils that respond best to routine and tact.",
                    "traits": ["precise", "alert", "dryly funny"],
                    "troubles": ["Needs help checking why supplies keep vanishing from the annex cupboards."],
                    "secrets": ["Has quietly reopened more of the annex than she was told to."],
                },
                {
                    "name": "Orin Pike",
                    "title": "Seventh-Year Prefect",
                    "faction": "Students",
                    "summary": "A capable student who knows how to look responsible while still being curious enough to open the wrong door.",
                    "traits": ["clever", "restless", "socially careful"],
                    "troubles": ["Wants to know who has been using the gallery after hours."],
                    "secrets": ["Has already found one way into the annex that is not on any school map."],
                },
            ],
            "rumor": "Someone says the annex has started opening its doors in a different order after dark.",
        }

    def generate_local_npc(self, location: LocationProfile, existing_names: list[str]) -> dict:
        instructions = (
            "Create one non-canon but lore-compatible Harry Potter world NPC in strict JSON with keys: "
            "name, title, faction, summary, traits, troubles, secrets."
        )
        prompt = (
            f"Location: {location.name}\n"
            f"Region: {location.region}\n"
            f"Kind: {location.kind}\n"
            f"Atmosphere: {', '.join(location.atmosphere)}\n"
            f"Existing names nearby: {', '.join(existing_names) or 'none'}"
        )
        raw = self.client.text(instructions=instructions, prompt=prompt, temperature=0.95)
        if raw:
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
        role_map = {
            "castle": ("Portrait Curator", "Hogwarts Staff"),
            "classroom": ("Fifth-Year Student", "Students"),
            "dungeons": ("Stores Monitor", "Hogwarts Staff"),
            "grounds": ("Groundskeeper's Helper", "Hogwarts Staff"),
            "forest": ("Centaur Watcher", "Forest"),
            "village": ("Shop Clerk", "Hogsmeade"),
            "street": ("Apprentice Shopkeeper", "Diagon Alley"),
        }
        title, faction = role_map.get(location.kind, ("Bystander", "Students"))
        base_name = choice(["Mira Vane", "Edgar Pike", "Tilda March", "Bram Cresswell", "Iris Flint", "Jonah Bell", "Nell Rowan"])
        if base_name in existing_names:
            base_name = f"{base_name} {len(existing_names) + 1}"
        return {
            "name": base_name,
            "title": title,
            "faction": faction,
            "summary": f"A person shaped by the habits and small pressures of {location.name.lower()}, always listening for who should not be there.",
            "traits": ["watchful", "capable", "hard to surprise"],
            "troubles": [f"Needs help untangling a quiet problem tied to {location.name}."],
            "secrets": [f"Knows something about the unseen traffic through {location.region}."],
        }

    def generate_area_npc(self, location: LocationProfile, area: AreaProfile, existing_names: list[str]) -> dict:
        raw = self.generate_local_npc(location, existing_names)
        raw["summary"] = f"A person shaped by the habits of {area.name.lower()}, used to noticing what changes in a room before anyone admits it has."
        raw["troubles"] = [f"Needs help with a private complication centered on {area.name}."]
        raw["secrets"] = [f"Knows something withheld inside {area.name}."]
        return raw

    @staticmethod
    def _fallback_location(
        location: LocationProfile,
        npcs: list[NpcState],
        shops: list[ShopProfile],
        rumors: list[Rumor],
        missions: list[Mission],
    ) -> str:
        mood = ", ".join(location.atmosphere[:3])
        people = f" Nearby stand {', '.join(npc.name for npc in npcs[:3])}." if npcs else ""
        shops_line = f" Trade or service gathers around {', '.join(shop.name for shop in shops[:2])}." if shops else ""
        rumor_line = f" The place carries rumor: {rumors[0].text}" if rumors else ""
        mission_line = f" Pressure gathers around {missions[0].title}." if missions else ""
        return (
            f"{location.summary} The place feels {mood}, and each moving stair, changing light, and held-back conversation suggests "
            "there is more going on here than anyone intends to explain directly."
            f"{people}{shops_line}{rumor_line}{mission_line}"
        )

    @staticmethod
    def _fallback_area(
        location: LocationProfile,
        area: AreaProfile,
        npcs: list[NpcState],
        shops: list[ShopProfile],
        rumors: list[Rumor],
        missions: list[Mission],
    ) -> str:
        mood = ", ".join(area.atmosphere[:3])
        people = f" Nearby stand {', '.join(npc.name for npc in npcs[:3])}." if npcs else ""
        shops_line = f" Trade or service here centers on {', '.join(shop.name for shop in shops[:2])}." if shops else ""
        rumor_line = f" The local air carries pressure from {rumors[0].text}" if rumors else ""
        mission_line = f" The place now feels tied to {missions[0].title}." if missions else ""
        return (
            f"{area.summary} Inside {location.name}, this smaller space feels {mood}. "
            "Details matter here: which object has been moved, which portrait is awake, and who has paused speaking just a little too quickly."
            f"{people}{shops_line}{rumor_line}{mission_line}"
        )

    @staticmethod
    def _fallback_speech(npc: NpcState, player_line: str) -> str:
        lowered = player_line.lower()
        if "forest" in lowered or "forbidden" in lowered:
            return "People talk about the forest as if it begins at the trees. Usually it starts earlier than that."
        if "secret" in lowered or "passage" in lowered:
            return "At Hogwarts, the difference between a secret and a route is often just whether you have found it yet."
        if "trouble" in lowered or "problem" in lowered:
            return "There is always some trouble. The interesting part is who has decided not to report it."
        if npc.troubles:
            return "I've my own concerns, same as anyone else here. Some of them are easier discussed away from the busiest corridor."
        return "People say all sorts of things in this castle. The useful part is noticing what they lower their voices for."


def _slug(text: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in text)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")
