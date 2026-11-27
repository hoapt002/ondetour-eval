"""Render the backend prompts exactly as goroute's AiTripServiceImpl does.

Java composition (see prompts/README.md):
    system = AI_TRIP_SYSTEM_CONTEXT + <task block> + "\n" + claudeLanguageRule()
    user   = <task template>.formatted(...)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Any

from .paths import PROMPTS_DIR

TASKS = ("rank", "order", "tips")

# AiTripLanguageSupport.displayName / normalize
_LANGUAGE_NAMES = {
    "vi": "Vietnamese",
    "ko": "Korean",
    "th": "Thai",
    "ja": "Japanese",
    "zh-TW": "Traditional Chinese",
    "ru": "Russian",
    "hi": "Hindi",
}

# Field order of AiTripCandidateResponse — Jackson serialises in declaration order, nulls included.
CANDIDATE_FIELDS = (
    "id",
    "sourceType",
    "sourceId",
    "name",
    "description",
    "address",
    "lat",
    "lng",
    "rating",
    "reviewCount",
    "photoUrl",
    "placeGroup",
    "category",
    "visitDurationMinutes",
    "durationText",
    "bookingId",
    "bookingSource",
    "priceAmount",
    "priceCurrency",
    "aiReason",
)


def normalize_locale(code: str | None) -> str:
    if code is None:
        return "en"
    c = code.strip()
    if c.lower() in ("zh-tw", "zh"):
        return "zh-TW"
    return c.lower()


def language_name(code: str | None) -> str:
    return _LANGUAGE_NAMES.get(normalize_locale(code), "English")


def normalize_pace(pace: str | None) -> str:
    if pace is None or not pace.strip():
        return "BALANCED"
    value = pace.strip().upper()
    return value if value in ("RELAXED", "EAGER") else "BALANCED"


def java_json(value: Any) -> str:
    """Compact JSON like `new ObjectMapper().writeValueAsString` (UTF-8, no spaces)."""
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def java_str(value: Any) -> str:
    """String.format("%s") of a Java value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def trim_text(value: str | None, max_length: int) -> str | None:
    """AiTripServiceImpl.trimText."""
    if value is None or not value.strip():
        return None
    normalized = value.strip()
    return normalized if len(normalized) <= max_length else normalized[: max_length - 3] + "..."


def candidate_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    return {field: candidate.get(field) for field in CANDIDATE_FIELDS}


def tips_payload(case: dict[str, Any]) -> list[dict[str, Any]]:
    """Rows built in generateVisitTips (insertion order matters)."""
    rows = []
    for c in case["candidates"]:
        rows.append(
            {
                "id": c["id"],
                "name": c.get("name"),
                "placeGroup": c.get("placeGroup"),
                "category": c.get("category"),
                "sourceType": c.get("sourceType"),
                "description": trim_text(c.get("description"), 120),
                "address": c.get("address"),
                "rating": c.get("rating"),
                "dayNumber": c["dayNumber"],
                "startTime": c["startTime"],
                "endTime": c["endTime"],
                "transportModeToHere": c.get("transportModeToHere"),
            }
        )
    return rows


# Fields that carry raw UUIDs; dropped in alias mode so the model only ever sees the short alias.
_UUID_FIELDS = ("sourceId", "bookingId", "photoUrl")


def alias_table(case: dict[str, Any]) -> dict[str, str]:
    """real id -> short alias (c1, c2, ...) in input order; duplicate ids share one alias."""
    table: dict[str, str] = {}
    for c in case["candidates"]:
        table.setdefault(c["id"], f"c{len(table) + 1}")
    return table


@dataclass(frozen=True)
class RenderedPrompt:
    system: str
    user: str
    # alias -> real id when the prompt version uses id_mode=alias (backend maps back the same way).
    aliases: dict[str, str] = field(default_factory=dict)

    @property
    def sha(self) -> str:
        return hashlib.sha256(f"{self.system}\x00{self.user}".encode()).hexdigest()


class PromptSet:
    def __init__(self, version: str = "v1", root: Path = PROMPTS_DIR):
        self.version = version
        self.dir = root / version
        if not self.dir.is_dir():
            raise FileNotFoundError(f"prompt version not found: {self.dir}")
        config_file = self.dir / "config.json"
        self.config: dict[str, Any] = json.loads(config_file.read_text("utf-8")) if config_file.exists() else {}
        self.id_mode = self.config.get("id_mode", "full")
        if self.id_mode not in ("full", "alias"):
            raise ValueError(f"{config_file}: id_mode must be 'full' or 'alias'")

    def _read(self, rel: str) -> str:
        return (self.dir / rel).read_text(encoding="utf-8")

    def fingerprint(self) -> str:
        h = hashlib.sha256()
        for path in sorted([*self.dir.rglob("*.txt"), *self.dir.glob("config.json")]):
            h.update(path.relative_to(self.dir).as_posix().encode())
            h.update(path.read_bytes())
        return h.hexdigest()[:12]

    def render(self, case: dict[str, Any]) -> RenderedPrompt:
        task = case["task"]
        if task not in TASKS:
            raise ValueError(f"unknown task {task!r}")
        trip = case["trip"]
        locale = normalize_locale(case.get("locale"))
        language_rule = Template(self._read("common/language_rule.txt")).substitute(
            language_name=language_name(locale), locale=locale
        )
        system = self._read("common/system_context.txt") + self._read(f"{task}/system.txt") + "\n" + language_rule

        prefs = trip.get("preferences")
        rows = tips_payload(case) if task == "tips" else [candidate_payload(c) for c in case["candidates"]]
        aliases: dict[str, str] = {}
        if self.id_mode == "alias":
            table = alias_table(case)
            aliases = {a: real for real, a in table.items()}
            rows = [
                {k: (table[v] if k == "id" else v) for k, v in row.items() if k not in _UUID_FIELDS} for row in rows
            ]
        candidates_json = java_json(rows)
        values = {
            "city": java_str(trip["city"]),
            "lat": java_str(trip.get("lat")),
            "lng": java_str(trip.get("lng")),
            "start_date": trip["startDate"],
            "end_date": trip["endDate"],
            "day_count": str(trip["dayCount"]),
            "pace": normalize_pace(trip.get("pace")),
            "preferences": "none" if prefs is None else prefs,
            "candidates": candidates_json,
        }
        user = Template(self._read(f"{task}/user.txt")).substitute(values)
        return RenderedPrompt(system=system, user=user, aliases=aliases)
