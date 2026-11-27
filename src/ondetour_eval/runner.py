from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .checks import grade
from .paths import CACHE_DIR, DATASETS_DIR, RUNS_DIR
from .prompts import PromptSet
from .providers import Completion, Provider


def load_cases(paths: list[Path] | None = None) -> list[dict[str, Any]]:
    files = paths or sorted(DATASETS_DIR.glob("*.jsonl"))
    cases: list[dict[str, Any]] = []
    for path in files:
        with path.open(encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if line.strip():
                    case = json.loads(line)
                    case.setdefault("_source", f"{path.name}:{n}")
                    cases.append(case)
    ids = [c["id"] for c in cases]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"duplicate case ids: {sorted(dupes)}")
    return cases


@dataclass
class RunConfig:
    provider: Provider
    prompt_version: str = "v1"
    repeats: int = 1
    concurrency: int = 6
    use_cache: bool = True
    threshold: float = 0.98
    label: str | None = None


def _cache_key(provider: Provider, rendered_sha: str, repeat: int) -> str:
    return hashlib.sha256(f"{provider.name}|{provider.model}|{rendered_sha}|{repeat}".encode()).hexdigest()


def _call(cfg: RunConfig, prompts: PromptSet, case: dict[str, Any], repeat: int) -> dict[str, Any]:
    rendered = prompts.render(case)
    key = f"{case['id']}#r{repeat}"
    cache_file = CACHE_DIR / f"{_cache_key(cfg.provider, rendered.sha, repeat)}.json"
    cached = False
    if cfg.use_cache and cfg.provider.name != "replay" and cache_file.exists():
        comp = Completion(**json.loads(cache_file.read_text(encoding="utf-8")))
        cached = True
    else:
        comp = cfg.provider.complete_with_retry(rendered, key)
        if comp.text is not None and cfg.provider.name != "replay":
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(json.dumps(comp.__dict__, ensure_ascii=False), encoding="utf-8")
    g = grade(case, comp.text, rendered.aliases)
    return {
        "key": key,
        "case_id": case["id"],
        "repeat": repeat,
        "task": case["task"],
        "category": case.get("category", "golden"),
        "locale": case.get("locale", "en"),
        "tags": case.get("tags", []),
        "prompt_sha": rendered.sha[:12],
        "cached": cached,
        "raw": comp.text,
        "provider_error": comp.error,
        "latency_s": round(comp.latency_s, 2),
        "input_tokens": comp.input_tokens,
        "output_tokens": comp.output_tokens,
        "served_model": comp.model,
        **g.to_dict(),
    }


def run(cfg: RunConfig, cases: list[dict[str, Any]], out_root: Path = RUNS_DIR) -> tuple[Path, dict[str, Any]]:
    prompts = PromptSet(cfg.prompt_version)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_model = cfg.provider.model.replace("/", "_")
    out_dir = out_root / f"{stamp}_{cfg.prompt_version}_{safe_model}" if not cfg.label else out_root / cfg.label
    out_dir.mkdir(parents=True, exist_ok=True)

    jobs = [(c, r) for c in cases for r in range(cfg.repeats)]
    results: list[dict[str, Any]] = []
    lock = threading.Lock()
    done = 0
    partial = out_dir / "results.partial.jsonl"
    with ThreadPoolExecutor(max_workers=cfg.concurrency) as pool, partial.open("w", encoding="utf-8") as live:
        futures = [pool.submit(_call, cfg, prompts, c, r) for c, r in jobs]
        for fut in as_completed(futures):
            row = fut.result()
            with lock:
                results.append(row)
                live.write(json.dumps(row, ensure_ascii=False) + "\n")
                live.flush()
                done += 1
                mark = "ok " if row["schema_valid"] else "BAD"
                why = "" if row["schema_valid"] else f"  {_why(row)[:120]}"
                print(f"[{done:>4}/{len(jobs)}] {mark} {row['key']}{why}", file=sys.stderr, flush=True)
    partial.unlink()

    order = {c["id"]: i for i, c in enumerate(cases)}
    results.sort(key=lambda r: (order[r["case_id"]], r["repeat"]))
    with (out_dir / "results.jsonl").open("w", encoding="utf-8") as fh:
        for row in results:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = summarize(results, cfg, prompts)
    (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "report.md").write_text(render_report(summary, results), encoding="utf-8")
    return out_dir, summary


def _why(row: dict[str, Any]) -> str:
    return row["provider_error"] or row["parse_error"] or "; ".join(row["schema_errors"][:3])


def _rate(rows: list[dict[str, Any]], key: str) -> float:
    return round(sum(1 for r in rows if r[key]) / len(rows), 4) if rows else 0.0


def summarize(results: list[dict[str, Any]], cfg: RunConfig, prompts: PromptSet) -> dict[str, Any]:
    def breakdown(field: str) -> dict[str, Any]:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in results:
            groups[str(r[field])].append(r)
        return {k: {"n": len(v), "schema_valid": _rate(v, "schema_valid")} for k, v in sorted(groups.items())}

    quality: dict[str, list[bool]] = defaultdict(list)
    for r in results:
        for name, ok in r["quality"].items():
            quality[name].append(ok)
    latencies = [r["latency_s"] for r in results if not r["cached"] and r["latency_s"]]
    schema_rate = _rate(results, "schema_valid")
    served = sorted({r["served_model"] for r in results if r["served_model"]})
    return {
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "provider": cfg.provider.name,
        "model": cfg.provider.model,
        "served_models": served,
        "prompt_version": cfg.prompt_version,
        "prompt_fingerprint": prompts.fingerprint(),
        "repeats": cfg.repeats,
        "n_cases": len({r["case_id"] for r in results}),
        "n_calls": len(results),
        "threshold": cfg.threshold,
        "schema_valid_rate": schema_rate,
        "passed": schema_rate >= cfg.threshold,
        "parsed_rate": _rate(results, "parsed"),
        "strict_json_rate": _rate(results, "strict_json"),
        "provider_errors": sum(1 for r in results if r["raw"] is None),
        "by_task": breakdown("task"),
        "by_category": breakdown("category"),
        "by_locale": breakdown("locale"),
        "quality": {k: {"n": len(v), "pass_rate": round(sum(v) / len(v), 4)} for k, v in sorted(quality.items())},
        "latency_s": {
            "p50": round(statistics.median(latencies), 2) if latencies else None,
            "p95": round(sorted(latencies)[math.ceil(0.95 * len(latencies)) - 1], 2) if latencies else None,
        },
        "tokens": {
            "input": sum(r["input_tokens"] or 0 for r in results),
            "output": sum(r["output_tokens"] or 0 for r in results),
        },
        "failures": [r["key"] for r in results if not r["schema_valid"]],
    }


def render_report(summary: dict[str, Any], results: list[dict[str, Any]]) -> str:
    pct = lambda x: f"{x * 100:.1f}%"  # noqa: E731
    verdict = "PASS" if summary["passed"] else "FAIL"
    lines = [
        f"# Eval report — {verdict}",
        "",
        f"- Provider / model: `{summary['provider']}` / `{summary['model']}`"
        + (f" (served: {', '.join(summary['served_models'])})" if summary["served_models"] else ""),
        f"- Prompt: `{summary['prompt_version']}` (fingerprint `{summary['prompt_fingerprint']}`)",
        f"- Cases: {summary['n_cases']} × {summary['repeats']} repeat(s) = {summary['n_calls']} calls",
        f"- **Schema-valid: {pct(summary['schema_valid_rate'])}** (gate ≥ {pct(summary['threshold'])})",
        f"- Parsed by backend: {pct(summary['parsed_rate'])} · strict JSON (no prose/fences): "
        f"{pct(summary['strict_json_rate'])} · provider errors: {summary['provider_errors']}",
        f"- Latency p50/p95: {summary['latency_s']['p50']}s / {summary['latency_s']['p95']}s · "
        f"tokens in/out: {summary['tokens']['input']:,} / {summary['tokens']['output']:,}",
        "",
    ]
    for title, key in (("Task", "by_task"), ("Category", "by_category"), ("Locale", "by_locale")):
        lines += [f"## By {title.lower()}", "", f"| {title} | n | schema-valid |", "|---|---:|---:|"]
        lines += [f"| {k} | {v['n']} | {pct(v['schema_valid'])} |" for k, v in summary[key].items()]
        lines.append("")
    lines += ["## Quality checks (not gating)", "", "| Check | n | pass |", "|---|---:|---:|"]
    lines += [f"| {k} | {v['n']} | {pct(v['pass_rate'])} |" for k, v in summary["quality"].items()]
    lines.append("")
    bad = [r for r in results if not r["schema_valid"]]
    lines += [f"## Schema failures ({len(bad)})", ""]
    for r in bad:
        why = _why(r)
        snippet = (r["raw"] or "").strip().replace("\n", " ")[:240]
        lines += [f"- `{r['key']}` ({r['task']}, {r['locale']}): {why}", f"  - raw: `{snippet}`"]
    soft = [(r, k) for r in results for k, ok in r["quality"].items() if not ok]
    lines += ["", f"## Quality misses ({len(soft)})", ""]
    for r, k in soft[:80]:
        note = r["notes"].get(k, "")
        lines.append(f"- `{r['key']}` — {k}" + (f" ({note})" if note else ""))
    return "\n".join(lines) + "\n"


def compare(base_dir: Path, new_dir: Path) -> str:
    def load(d: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
        summary = json.loads((d / "summary.json").read_text(encoding="utf-8"))
        rows = {}
        with (d / "results.jsonl").open(encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                rows[row["key"]] = row
        return summary, rows

    (s1, r1), (s2, r2) = load(base_dir), load(new_dir)
    pct = lambda x: f"{x * 100:.1f}%"  # noqa: E731
    out = [
        f"base: {s1['prompt_version']}/{s1['model']} ({base_dir.name})",
        f"new:  {s2['prompt_version']}/{s2['model']} ({new_dir.name})",
        "",
    ]
    for key in ("schema_valid_rate", "parsed_rate", "strict_json_rate"):
        out.append(f"{key:<20} {pct(s1[key]):>7} → {pct(s2[key]):>7}  ({(s2[key] - s1[key]) * 100:+.1f} pp)")
    for name in sorted(set(s1["quality"]) | set(s2["quality"])):
        a = s1["quality"].get(name, {}).get("pass_rate")
        b = s2["quality"].get(name, {}).get("pass_rate")
        if a is not None and b is not None:
            out.append(f"{name:<36} {pct(a):>7} → {pct(b):>7}  ({(b - a) * 100:+.1f} pp)")
    common = set(r1) & set(r2)
    regressed = sorted(k for k in common if r1[k]["schema_valid"] and not r2[k]["schema_valid"])
    fixed = sorted(k for k in common if not r1[k]["schema_valid"] and r2[k]["schema_valid"])
    out += [
        "",
        f"regressed ({len(regressed)}): {', '.join(regressed) or '-'}",
        f"fixed ({len(fixed)}): {', '.join(fixed) or '-'}",
    ]
    return "\n".join(out)
