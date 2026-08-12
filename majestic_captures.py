"""Majestic RP — family-wars API client and Alarm filter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import MAJESTIC_FAMILY_NAME, MAJESTIC_SERVER_ID
from family_registry import FamilySide, lookup_side
from majestic_api import MajesticApiError, MajesticRateLimitError, majestic_request

__all__ = [
    "CaptEvent",
    "MajesticApiError",
    "MajesticRateLimitError",
    "fetch_family_wars",
    "filter_family_captures",
    "make_test_event",
    "parse_capt_event",
    "family_matches",
]


@dataclass(frozen=True)
class CaptEvent:
    record_id: int
    capture_id: int
    side: str  # our side: "attack" | "defense"
    attacker: FamilySide
    defender: FamilySide
    zone_id: int | None
    start_at: str
    status: str

    @property
    def is_attack(self) -> bool:
        return self.side == "attack"

    @property
    def is_defense(self) -> bool:
        return self.side == "defense"

    @property
    def our_family(self) -> str:
        return self.attacker.name if self.is_attack else self.defender.name

    @property
    def enemy(self) -> str:
        return self.defender.name if self.is_attack else self.attacker.name


def _norm(value: str | None) -> str:
    return (value or "").strip().casefold()


def family_matches(name: str | None, family: str) -> bool:
    if not name or not family:
        return False
    a = _norm(name)
    b = _norm(family)
    return a == b or b in a or a in b


def fetch_family_wars(server_id: str | None = None) -> list[dict[str, Any]]:
    sid = server_id or MAJESTIC_SERVER_ID
    result = majestic_request(f"/v1/ext/family-wars/{sid}")
    captures = result.get("captures") or []
    if not isinstance(captures, list):
        return []
    return captures


def parse_capt_event(raw: dict[str, Any], family: str | None = None) -> CaptEvent | None:
    fam = family or MAJESTIC_FAMILY_NAME
    attackers_name = raw.get("attackersName")
    defenders_name = raw.get("defendersName")

    side: str | None = None
    if family_matches(attackers_name, fam):
        side = "attack"
    elif family_matches(defenders_name, fam):
        side = "defense"
    else:
        return None

    record_id = raw.get("id")
    if record_id is None:
        return None

    attacker = lookup_side(family_id=_int_or_none(raw.get("attackersId")), name=attackers_name)
    defender = lookup_side(family_id=_int_or_none(raw.get("defendersId")), name=defenders_name)

    if attackers_name and attacker.name == "—":
        attacker = FamilySide(family_id=attacker.family_id, name=str(attackers_name))
    if defenders_name and defender.name == "—":
        defender = FamilySide(family_id=defender.family_id, name=str(defenders_name))

    return CaptEvent(
        record_id=int(record_id),
        capture_id=int(raw.get("captureId") or 0),
        side=side,
        attacker=attacker,
        defender=defender,
        zone_id=int(raw["gangZoneId"]) if raw.get("gangZoneId") is not None else None,
        start_at=str(raw.get("startAt") or ""),
        status=str(raw.get("status") or ""),
    )


def _int_or_none(value: Any) -> int | None:
    if value is None or value == -1 or value == "-1":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def filter_family_captures(
    captures: list[dict[str, Any]],
    family: str | None = None,
) -> list[CaptEvent]:
    out: list[CaptEvent] = []
    for raw in captures:
        ev = parse_capt_event(raw, family)
        if ev:
            out.append(ev)
    return out


def make_test_event(side: str, family: str | None = None) -> CaptEvent:
    fam = family or MAJESTIC_FAMILY_NAME
    alarm = lookup_side(family_id=None, name=fam)
    if alarm.name == "—":
        alarm = FamilySide(family_id=None, name=fam, tag=fam[:4].upper(), color="#c0392b", has_logo=False)
    spartan = lookup_side(family_id=730, name="SPARTAN")
    thugger = lookup_side(family_id=5, name="THUGGER")

    if side == "attack":
        return CaptEvent(
            record_id=-1,
            capture_id=9999,
            side="attack",
            attacker=alarm,
            defender=spartan,
            zone_id=1967,
            start_at="2026-08-12T00:00:00.000Z",
            status="active",
        )
    return CaptEvent(
        record_id=-2,
        capture_id=9998,
        side="defense",
        attacker=thugger,
        defender=alarm,
        zone_id=4758,
        start_at="2026-08-12T00:00:00.000Z",
        status="active",
    )
