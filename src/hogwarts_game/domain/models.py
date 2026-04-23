from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PlayerProfile:
    name: str
    title: str
    summary: str
    voice_notes: list[str]
    starting_inventory: list[str]


@dataclass
class ShopProfile:
    id: str
    name: str
    owner: str
    location_id: str
    flavor: str
    area_id: str = ""
    interior_area_id: str = ""
    goods: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ShopProfile":
        return cls(**data)


@dataclass
class LocationProfile:
    id: str
    name: str
    region: str
    kind: str
    summary: str
    atmosphere: list[str]
    sensory_details: list[str] = field(default_factory=list)
    landmarks: list[str] = field(default_factory=list)
    linked_locations: list[str] = field(default_factory=list)
    resident_npcs: list[str] = field(default_factory=list)
    shop_ids: list[str] = field(default_factory=list)
    rumor_tags: list[str] = field(default_factory=list)
    travel_keywords: list[str] = field(default_factory=list)
    can_expand: bool = False
    generated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LocationProfile":
        return cls(**data)


@dataclass
class AreaProfile:
    id: str
    name: str
    parent_location_id: str
    summary: str
    atmosphere: list[str]
    landmarks: list[str] = field(default_factory=list)
    linked_areas: list[str] = field(default_factory=list)
    resident_npcs: list[str] = field(default_factory=list)
    shop_ids: list[str] = field(default_factory=list)
    rumor_tags: list[str] = field(default_factory=list)
    travel_keywords: list[str] = field(default_factory=list)
    generated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AreaProfile":
        return cls(**data)


@dataclass
class NpcState:
    name: str
    title: str
    faction: str
    summary: str
    speech_style: list[str]
    traits: list[str]
    home_location: str
    current_location: str
    home_area: str = ""
    current_area: str = ""
    shop_id: str = ""
    canonical: bool = False
    generated: bool = False
    disposition: int = 0
    troubles: list[str] = field(default_factory=list)
    secrets: list[str] = field(default_factory=list)
    rumor_ids: list[str] = field(default_factory=list)
    memory: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NpcState":
        data.setdefault("home_area", "")
        data.setdefault("current_area", "")
        data.setdefault("shop_id", "")
        data.setdefault("canonical", False)
        data.setdefault("generated", False)
        data.setdefault("disposition", 0)
        data.setdefault("troubles", [])
        data.setdefault("secrets", [])
        data.setdefault("rumor_ids", [])
        data.setdefault("memory", [])
        return cls(**data)


@dataclass
class Rumor:
    id: str
    text: str
    source: str
    location_id: str
    topic: str
    leads_to: str = ""
    person_hint: str = ""
    discovered: bool = False
    resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Rumor":
        data.setdefault("leads_to", "")
        data.setdefault("person_hint", "")
        data.setdefault("discovered", False)
        data.setdefault("resolved", False)
        return cls(**data)


@dataclass
class Mission:
    id: str
    title: str
    description: str
    giver: str
    location_id: str
    kind: str
    notes: list[str] = field(default_factory=list)
    status: str = "active"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Mission":
        data.setdefault("notes", [])
        data.setdefault("status", "active")
        return cls(**data)


@dataclass
class ParsedCommand:
    kind: str
    raw: str
    target: str | None = None
    topic: str | None = None


@dataclass
class GameState:
    player_name: str
    player_title: str
    location_id: str
    time_index: int
    inventory: list[str]
    area_id: str = ""
    discovered_locations: list[str] = field(default_factory=list)
    discovered_areas: list[str] = field(default_factory=list)
    visited_locations: list[str] = field(default_factory=list)
    known_people: list[str] = field(default_factory=list)
    heard_rumor_ids: list[str] = field(default_factory=list)
    journal: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    faction_trust: dict[str, int] = field(default_factory=dict)
    npc_states: dict[str, dict[str, Any]] = field(default_factory=dict)
    rumors: list[dict[str, Any]] = field(default_factory=list)
    missions: list[dict[str, Any]] = field(default_factory=list)
    dynamic_locations: dict[str, dict[str, Any]] = field(default_factory=dict)
    dynamic_shops: dict[str, dict[str, Any]] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    last_narration: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        data.setdefault("area_id", "")
        data.setdefault("discovered_locations", [])
        data.setdefault("discovered_areas", [])
        data.setdefault("visited_locations", [])
        data.setdefault("known_people", [])
        data.setdefault("heard_rumor_ids", [])
        data.setdefault("journal", [])
        data.setdefault("facts", [])
        data.setdefault("faction_trust", {})
        data.setdefault("npc_states", {})
        data.setdefault("rumors", [])
        data.setdefault("missions", [])
        data.setdefault("dynamic_locations", {})
        data.setdefault("dynamic_shops", {})
        data.setdefault("suggestions", [])
        data.setdefault("last_narration", "")
        return cls(**data)
