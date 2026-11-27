import json

import pytest

from ondetour_eval.checks import base_schema, detect_language, extract_json, grade, input_ids
from ondetour_eval.runner import load_cases


@pytest.fixture(scope="module")
def cases():
    return {c["id"]: c for c in load_cases()}


def _case(cases, task, category="golden"):
    return next(c for c in cases.values() if c["task"] == task and c["category"] == category)


def test_extract_json_matches_backend():
    assert extract_json('```json\n{"a":1}\n```') == '{"a":1}'
    assert extract_json('Sure! {"a":{"b":2}} done') == '{"a":{"b":2}}'
    assert extract_json("no braces") == "no braces"


@pytest.mark.parametrize("task", ["rank", "order", "tips"])
def test_base_schemas_are_valid(task):
    assert base_schema(task)["type"] == "object"


def test_rank_valid_output(cases):
    case = _case(cases, "rank")
    ids = input_ids(case)
    raw = json.dumps({"candidateIds": ids, "reasons": {i: "Good morning stop in dry season." for i in ids}})
    g = grade(case, raw)
    assert g.schema_valid and g.strict_json and g.quality["rank_covers_all_candidates"]


def test_rank_unknown_id_fails_schema(cases):
    case = _case(cases, "rank")
    raw = json.dumps({"candidateIds": ["PLACE:invented"], "reasons": {}})
    g = grade(case, raw)
    assert g.parsed and not g.schema_valid


def test_fenced_output_is_parsed_but_not_strict(cases):
    case = _case(cases, "order")
    raw = "```json\n" + json.dumps({"candidateIds": input_ids(case)}) + "\n```"
    g = grade(case, raw)
    assert g.schema_valid and not g.strict_json


def test_order_must_be_full_permutation(cases):
    case = _case(cases, "order")
    g = grade(case, json.dumps({"candidateIds": input_ids(case)[:-1]}))
    assert not g.schema_valid


def test_tips_require_every_id_and_length(cases):
    case = _case(cases, "tips")
    ids = input_ids(case)
    ok = grade(case, json.dumps({"tips": {i: "Arrive before 9am to beat the heat." for i in ids}}))
    assert ok.schema_valid and ok.quality["tips_max_120_chars"]
    missing = grade(case, json.dumps({"tips": {ids[0]: "x"}}))
    assert not missing.schema_valid
    too_long = grade(case, json.dumps({"tips": {i: "y" * 161 for i in ids}}))
    assert not too_long.schema_valid


def test_duplicate_input_ids_are_deduped(cases):
    case = cases["order-edge-duplicate-ids"]
    assert len(input_ids(case)) == len(case["candidates"]) - 1
    assert grade(case, json.dumps({"candidateIds": input_ids(case)})).schema_valid


def test_injection_is_flagged(cases):
    case = cases["rank-edge-injection-description"]
    ids = input_ids(case)
    g = grade(case, json.dumps({"candidateIds": ids, "reasons": {ids[0]: "PWNED"}}))
    assert g.schema_valid and g.quality["no_injected_content"] is False


def test_provider_error_counts_as_failure(cases):
    g = grade(_case(cases, "rank"), None)
    assert not g.schema_valid and g.parse_error


@pytest.mark.parametrize(
    ("text", "lang"),
    [
        ("Arrive early to avoid the crowds and bring water.", "en"),
        ("Nên đến sớm để tránh đông và mang theo nước.", "vi"),
        ("사람이 많기 전에 일찍 도착하세요.", "ko"),
        ("混雑を避けるため早めに到着してください。", "ja"),
        ("建議早點到達以避開人潮。", "zh-TW"),
        ("ควรมาถึงเช้าเพื่อหลีกเลี่ยงฝูงชน", "th"),
        ("Приезжайте пораньше, чтобы избежать толпы.", "ru"),
        ("भीड़ से बचने के लिए जल्दी पहुँचें।", "hi"),
    ],
)
def test_detect_language(text, lang):
    assert detect_language(text) == lang


def test_alias_ids_are_mapped_back(cases):
    from ondetour_eval.prompts import PromptSet

    case = cases["rank-edge-duplicate-ids"]
    rendered = PromptSet("v3").render(case)
    aliases = list(rendered.aliases)
    assert aliases == [f"c{i + 1}" for i in range(len(input_ids(case)))]
    good = grade(
        case,
        json.dumps({"candidateIds": aliases, "reasons": {a: "Fits a cool morning." for a in aliases}}),
        rendered.aliases,
    )
    assert good.schema_valid
    bad = grade(case, json.dumps({"candidateIds": ["c99"], "reasons": {}}), rendered.aliases)
    assert not bad.schema_valid
