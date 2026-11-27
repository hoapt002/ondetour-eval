import subprocess
import sys
from pathlib import Path

import pytest

from ondetour_eval.checks import case_schema, input_ids
from ondetour_eval.prompts import PromptSet
from ondetour_eval.runner import load_cases

ROOT = Path(__file__).resolve().parents[1]


def test_at_least_100_cases_with_edges():
    cases = load_cases()
    assert len(cases) >= 100
    assert sum(c["category"] == "edge" for c in cases) >= 40
    for task in ("rank", "order", "tips"):
        assert sum(c["task"] == task for c in cases) >= 30


@pytest.mark.parametrize("version", sorted(p.name for p in (ROOT / "prompts").iterdir() if p.is_dir()))
def test_every_case_renders_without_leftover_placeholders(version):
    prompts = PromptSet(version)
    for case in load_cases():
        rendered = prompts.render(case)
        assert "${" not in rendered.system and "${" not in rendered.user, case["id"]
        expected_id = "c1" if prompts.id_mode == "alias" else input_ids(case)[0]
        assert f'"id":"{expected_id}"' in rendered.user, case["id"]
        if prompts.id_mode == "alias":
            assert input_ids(case)[0].split(":", 1)[1] not in rendered.user, "raw uuid leaked in alias mode"
        case_schema(case)


def test_dataset_is_reproducible(tmp_path):
    before = {p.name: p.read_bytes() for p in (ROOT / "datasets").glob("*.jsonl")}
    subprocess.run([sys.executable, str(ROOT / "scripts/build_dataset.py")], check=True, capture_output=True)
    after = {p.name: p.read_bytes() for p in (ROOT / "datasets").glob("*.jsonl")}
    assert before == after, "datasets/ is stale: run scripts/build_dataset.py and commit the result"


def test_system_prompt_matches_java_composition():
    case = next(c for c in load_cases() if c["task"] == "rank" and c["locale"] == "ko")
    system = PromptSet("v1").render(case).system
    assert system.startswith("This is a travel planning app for foreign tourists visiting Vietnam.\n")
    assert "You rank real travel candidates" in system
    assert system.endswith(
        "Language: Respond ONLY in Korean (locale code: ko).\n"
        "All user-visible strings in JSON (reasons, tips, summaries) must use this language.\n"
        "Do not mix languages. Candidate names and addresses stay as provided in input.\n"
    )
