"""Grading: JSON parsing (backend-compatible), JSON Schema validation, and soft quality checks.

Gate metric = `schema_valid`: the output, parsed the way the backend parses it
(`AiTripServiceImpl.extractJson` + Jackson), validates against the case-specialised schema.
Everything else is a quality signal that is reported but does not fail the run.
"""

from __future__ import annotations

import copy
import json
import math
import re
import unicodedata
from dataclasses import dataclass, field
from functools import cache
from typing import Any

from jsonschema import Draft202012Validator

from .paths import SCHEMAS_DIR
from .prompts import normalize_locale

GENERIC_PHRASES = ("enjoy your visit", "have a great time", "have fun", "enjoy your stay")


# ---------------------------------------------------------------- parsing


def extract_json(raw: str) -> str:
    """Port of AiTripServiceImpl.extractJson: first '{' .. last '}'."""
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        return raw[start : end + 1]
    return raw


def parse_like_backend(raw: str) -> tuple[Any | None, str | None]:
    try:
        return json.loads(extract_json(raw)), None
    except (json.JSONDecodeError, ValueError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def is_strict_json(raw: str) -> bool:
    """True when the whole response is one JSON document (no prose, no ``` fences)."""
    try:
        json.loads(raw)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


# ---------------------------------------------------------------- schemas


@cache
def base_schema(task: str) -> dict[str, Any]:
    schema = json.loads((SCHEMAS_DIR / f"{task}.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def input_ids(case: dict[str, Any]) -> list[str]:
    """Distinct candidate IDs in input order (backend dedups with toMap(..., (a, b) -> a))."""
    return list(dict.fromkeys(c["id"] for c in case["candidates"]))


def case_schema(case: dict[str, Any]) -> dict[str, Any]:
    """Base schema tightened with the contract that depends on this case's input."""
    task = case["task"]
    ids = input_ids(case)
    schema = copy.deepcopy(base_schema(task))
    props = schema["properties"]
    if task == "rank":
        props["candidateIds"]["items"]["enum"] = ids
        props["candidateIds"]["maxItems"] = len(ids)
        props["reasons"]["propertyNames"] = {"enum": ids}
    elif task == "order":
        props["candidateIds"]["items"]["enum"] = ids
        props["candidateIds"]["minItems"] = len(ids)
        props["candidateIds"]["maxItems"] = len(ids)
    elif task == "tips":
        props["tips"]["propertyNames"] = {"enum": ids}
        props["tips"]["required"] = ids
    return schema


def schema_errors(case: dict[str, Any], doc: Any) -> list[str]:
    validator = Draft202012Validator(case_schema(case))
    errors = sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
    out = []
    for err in errors[:8]:
        path = "/".join(str(p) for p in err.absolute_path) or "<root>"
        out.append(f"{path}: {err.message[:200]}")
    return out


# ---------------------------------------------------------------- language

_VI_CHARS = set("ăâđêôơưĂÂĐÊÔƠƯ")
_VI_TONES = {"̀", "́", "̃", "̉", "̣"}


def _script_counts(text: str) -> dict[str, int]:
    counts = {"hangul": 0, "thai": 0, "kana": 0, "han": 0, "cyrillic": 0, "devanagari": 0, "latin": 0, "vi": 0}
    for ch in text:
        o = ord(ch)
        if 0xAC00 <= o <= 0xD7AF or 0x1100 <= o <= 0x11FF or 0x3130 <= o <= 0x318F:
            counts["hangul"] += 1
        elif 0x0E00 <= o <= 0x0E7F:
            counts["thai"] += 1
        elif 0x3040 <= o <= 0x30FF:
            counts["kana"] += 1
        elif 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF:
            counts["han"] += 1
        elif 0x0400 <= o <= 0x04FF:
            counts["cyrillic"] += 1
        elif 0x0900 <= o <= 0x097F:
            counts["devanagari"] += 1
        elif ch.isalpha() and o < 0x0250 or 0x1E00 <= o <= 0x1EFF:
            counts["latin"] += 1
            decomposed = unicodedata.normalize("NFD", ch)
            if ch in _VI_CHARS or any(m in _VI_TONES for m in decomposed[1:]):
                counts["vi"] += 1
    return counts


def detect_language(text: str) -> str:
    """Coarse script-based guess: en / vi / ko / th / ja / zh-TW / ru / hi / unknown."""
    c = _script_counts(text)
    letters = sum(v for k, v in c.items() if k != "vi")
    if letters == 0:
        return "unknown"
    if c["hangul"] / letters > 0.3:
        return "ko"
    if c["thai"] / letters > 0.3:
        return "th"
    if c["kana"] > 0 and (c["kana"] + c["han"]) / letters > 0.3:
        return "ja"
    if c["han"] / letters > 0.3:
        return "zh-TW"
    if c["cyrillic"] / letters > 0.3:
        return "ru"
    if c["devanagari"] / letters > 0.3:
        return "hi"
    if c["latin"] / letters > 0.5:
        return "vi" if c["vi"] / max(c["latin"], 1) > 0.06 else "en"
    return "unknown"


def strip_proper_names(text: str, case: dict[str, Any]) -> str:
    """Remove candidate names/addresses/city (allowed to stay Vietnamese) before language detection."""
    out = text
    tokens = [case["trip"]["city"]]
    for c in case["candidates"]:
        tokens += [c.get("name") or "", c.get("address") or ""]
    for token in sorted({t for t in tokens if t}, key=len, reverse=True):
        out = out.replace(token, " ")
    return out


def language_ok(texts: list[str], case: dict[str, Any]) -> tuple[bool, str]:
    expected = normalize_locale(case.get("locale"))
    if expected not in ("vi", "ko", "th", "ja", "zh-TW", "ru", "hi"):
        expected = "en"
    joined = " ".join(strip_proper_names(t, case) for t in texts)
    got = detect_language(joined)
    if got == "unknown":
        return True, "no letters to judge"
    return got == expected, f"expected {expected}, detected {got}"


# ---------------------------------------------------------------- geometry


def _haversine_km(a: dict[str, Any], b: dict[str, Any]) -> float:
    lat1, lng1, lat2, lng2 = map(math.radians, (a["lat"], a["lng"], b["lat"], b["lng"]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def path_km(stops: list[dict[str, Any]]) -> float:
    return sum(_haversine_km(stops[i], stops[i + 1]) for i in range(len(stops) - 1))


def nearest_neighbor_km(stops: list[dict[str, Any]]) -> float:
    if not stops:
        return 0.0
    remaining = stops[1:]
    route = [stops[0]]
    while remaining:
        nxt = min(remaining, key=lambda s: _haversine_km(route[-1], s))
        remaining.remove(nxt)
        route.append(nxt)
    return path_km(route)


# ---------------------------------------------------------------- grading


@dataclass
class Grade:
    parsed: bool = False
    strict_json: bool = False
    schema_valid: bool = False
    parse_error: str | None = None
    schema_errors: list[str] = field(default_factory=list)
    quality: dict[str, bool] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "parsed": self.parsed,
            "strict_json": self.strict_json,
            "schema_valid": self.schema_valid,
            "parse_error": self.parse_error,
            "schema_errors": self.schema_errors,
            "quality": self.quality,
            "notes": self.notes,
        }


def resolve_aliases(task: str, doc: Any, aliases: dict[str, str]) -> Any:
    """Map short aliases back to real ids, as the backend would; unknown values are left untouched."""
    if not aliases or not isinstance(doc, dict):
        return doc

    def real(value: Any) -> Any:
        return aliases.get(value, value) if isinstance(value, str) else value

    out = dict(doc)
    if isinstance(out.get("candidateIds"), list):
        out["candidateIds"] = [real(v) for v in out["candidateIds"]]
    for key in ("reasons", "tips"):
        if isinstance(out.get(key), dict):
            out[key] = {real(k): v for k, v in out[key].items()}
    return out


def grade(case: dict[str, Any], raw: str | None, aliases: dict[str, str] | None = None) -> Grade:
    g = Grade()
    if raw is None:
        g.parse_error = "no output (provider error)"
        return g
    g.strict_json = is_strict_json(raw.strip())
    doc, err = parse_like_backend(raw)
    if err is not None:
        g.parse_error = err
        return g
    g.parsed = True
    doc = resolve_aliases(case["task"], doc, aliases or {})
    g.schema_errors = schema_errors(case, doc)
    g.schema_valid = not g.schema_errors

    for needle in case.get("expect", {}).get("forbiddenSubstrings", []):
        ok = needle.lower() not in raw.lower()
        g.quality["no_injected_content"] = g.quality.get("no_injected_content", True) and ok
        if not ok:
            g.notes["no_injected_content"] = f"output contains {needle!r}"

    if not isinstance(doc, dict):
        return g
    task = case["task"]
    if task == "rank":
        _quality_rank(case, doc, g)
    elif task == "order":
        _quality_order(case, doc, g)
    elif task == "tips":
        _quality_tips(case, doc, g)
    return g


def _ids(doc: dict[str, Any]) -> list[str]:
    ids = doc.get("candidateIds")
    return [i for i in ids if isinstance(i, str)] if isinstance(ids, list) else []


def _quality_rank(case: dict[str, Any], doc: dict[str, Any], g: Grade) -> None:
    by_id = {c["id"]: c for c in case["candidates"]}
    ranked = [i for i in _ids(doc) if i in by_id]
    all_ids = input_ids(case)
    g.quality["rank_covers_all_candidates"] = set(ranked) == set(all_ids)

    non_accom = [c for c in case["candidates"] if c.get("placeGroup") != "ACCOMMODATION"]
    if len(non_accom) >= 3 and len(non_accom) < len(case["candidates"]):
        top = ranked[:3]
        g.quality["accommodation_not_in_top3"] = all(by_id[i].get("placeGroup") != "ACCOMMODATION" for i in top)

    reasons = doc.get("reasons") if isinstance(doc.get("reasons"), dict) else {}
    if ranked:
        covered = sum(1 for i in ranked if isinstance(reasons.get(i), str) and reasons[i].strip())
        g.quality["reasons_for_80pct"] = covered / len(ranked) >= 0.8
    texts = [v for v in reasons.values() if isinstance(v, str)]
    if texts:
        ok, note = language_ok(texts, case)
        g.quality["language_matches_locale"] = ok
        g.notes["language_matches_locale"] = note


def _quality_order(case: dict[str, Any], doc: dict[str, Any], g: Grade) -> None:
    by_id = {c["id"]: c for c in case["candidates"]}
    ordered = [by_id[i] for i in _ids(doc) if i in by_id]
    geo = [c for c in ordered if c.get("lat") is not None and c.get("lng") is not None]
    if len(geo) >= 4 and len(geo) == len(ordered):
        model_km = path_km(geo)
        nn_km = nearest_neighbor_km(list(geo))
        ok = model_km <= max(nn_km * 1.6, nn_km + 3.0)
        g.quality["route_within_1_6x_nearest_neighbor"] = ok
        g.notes["route_within_1_6x_nearest_neighbor"] = f"model {model_km:.1f} km vs NN {nn_km:.1f} km"


def _quality_tips(case: dict[str, Any], doc: dict[str, Any], g: Grade) -> None:
    tips = doc.get("tips") if isinstance(doc.get("tips"), dict) else {}
    texts = [v for v in tips.values() if isinstance(v, str)]
    if not texts:
        return
    g.quality["tips_max_120_chars"] = all(len(t) <= 120 for t in texts)
    g.quality["no_generic_phrases"] = not any(p in t.lower() for t in texts for p in GENERIC_PHRASES)
    descs = {c["id"]: (c.get("description") or "") for c in case["candidates"]}
    copied = [
        i
        for i, t in tips.items()
        if isinstance(t, str) and len(descs.get(i, "")) >= 30 and _norm(descs[i])[:40] in _norm(t)
    ]
    g.quality["no_copied_description"] = not copied
    ok, note = language_ok(texts, case)
    g.quality["language_matches_locale"] = ok
    g.notes["language_matches_locale"] = note


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()
