from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import json
from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

from hogwarts_game.domain.models import AreaProfile, LocationProfile, NpcState, PlayerProfile, Rumor, ShopProfile


@dataclass
class LoreCatalog:
    player: PlayerProfile
    locations: dict[str, LocationProfile]
    areas: dict[str, AreaProfile]
    npcs: dict[str, NpcState]
    rumors: list[Rumor]
    shops: dict[str, ShopProfile]

    @classmethod
    def load(cls) -> "LoreCatalog":
        base = Path(__file__).resolve().parents[1] / "content"
        locations_raw = _read_structured(base / "locations.yaml")
        areas_raw = _read_structured(base / "areas.yaml")
        npcs_raw = _read_structured(base / "npcs.yaml")
        rumors_raw = _read_structured(base / "rumors.yaml")
        shops_raw = _read_structured(base / "shops.yaml")
        player = PlayerProfile(**npcs_raw["player"])
        locations = {item["id"]: LocationProfile(**item) for item in locations_raw["locations"]}
        areas = {item["id"]: AreaProfile(**item) for item in areas_raw["areas"]}
        npcs = {
            item["name"]: NpcState(
                name=item["name"],
                title=item["title"],
                faction=item["faction"],
                summary=item["summary"],
                speech_style=item["speech_style"],
                traits=item["traits"],
                home_location=item["home_location"],
                current_location=item["home_location"],
                home_area=item.get("home_area", ""),
                current_area=item.get("home_area", ""),
                shop_id=item.get("shop_id", ""),
                canonical=item.get("canonical", False),
                troubles=item.get("troubles", []),
                secrets=item.get("secrets", []),
                rumor_ids=item.get("rumor_ids", []),
            )
            for item in npcs_raw["npcs"]
        }
        rumors = [Rumor(**item) for item in rumors_raw["rumors"]]
        shops = {item["id"]: ShopProfile(**item) for item in shops_raw["shops"]}
        return cls(player=player, locations=locations, areas=areas, npcs=npcs, rumors=rumors, shops=shops)

    def find_location(self, query: str, all_locations: dict[str, LocationProfile]) -> LocationProfile | None:
        needle = query.strip().lower()
        if not needle:
            return None
        if needle in all_locations:
            return all_locations[needle]
        for location in all_locations.values():
            haystacks = [
                location.id,
                location.name,
                location.region,
                *location.travel_keywords,
                *location.landmarks,
            ]
            if any(needle in value.lower() for value in haystacks):
                return location
        return None

    def find_area(
        self,
        query: str,
        all_areas: dict[str, AreaProfile],
        parent_location_id: str,
        allowed_area_ids: set[str] | None = None,
    ) -> AreaProfile | None:
        needle = query.strip().lower()
        if not needle:
            return None
        for area in all_areas.values():
            if area.parent_location_id != parent_location_id:
                continue
            if allowed_area_ids is not None and area.id not in allowed_area_ids:
                continue
            haystacks = [area.id, area.name, *area.travel_keywords, *area.landmarks]
            if any(needle in value.lower() for value in haystacks):
                return area
        return None

    def find_npc(
        self,
        query: str,
        npc_states: dict[str, NpcState],
        location_id: str | None = None,
        area_id: str | None = None,
    ) -> NpcState | None:
        needle = query.strip().lower()
        if not needle:
            return None
        candidates: list[NpcState] = []
        for npc in npc_states.values():
            if location_id and npc.current_location != location_id:
                continue
            if area_id is not None and npc.current_area != area_id:
                continue
            candidates.append(npc)
            if needle == npc.name.lower() or needle in npc.name.lower():
                return npc

        for npc in candidates:
            parts = [part.lower() for part in npc.name.split()]
            if any(part.startswith(needle) or needle.startswith(part) for part in parts):
                return npc

        scored: list[tuple[float, NpcState]] = []
        for npc in candidates:
            parts = [part.lower() for part in npc.name.split()]
            ratios = [SequenceMatcher(None, needle, npc.name.lower()).ratio()]
            ratios.extend(SequenceMatcher(None, needle, part).ratio() for part in parts)
            score = max(ratios)
            if score >= 0.72:
                scored.append((score, npc))
        if scored:
            scored.sort(key=lambda item: item[0], reverse=True)
            return scored[0][1]
        return None


def _read_structured(path: Path) -> dict:
    text = path.read_text()
    if yaml is not None:
        return yaml.safe_load(text)
    return json.loads(text)
