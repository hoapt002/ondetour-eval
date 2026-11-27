from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .paths import RUNS_DIR
from .prompts import PromptSet
from .providers import make_provider
from .runner import RunConfig, compare, load_cases, run


def _filter(cases, args):
    if args.task:
        cases = [c for c in cases if c["task"] in args.task]
    if args.category:
        cases = [c for c in cases if c.get("category") in args.category]
    if args.case:
        cases = [c for c in cases if any(sel in c["id"] for sel in args.case)]
    if args.limit:
        cases = cases[: args.limit]
    return cases


def cmd_run(args: argparse.Namespace) -> int:
    cases = _filter(load_cases([Path(p) for p in args.dataset] if args.dataset else None), args)
    if not cases:
        print("no cases selected", file=sys.stderr)
        return 2
    provider = make_provider(args.provider, args.model, Path(args.replay) if args.replay else None)
    cfg = RunConfig(
        provider=provider,
        prompt_version=args.prompt_version,
        repeats=args.repeats,
        concurrency=args.concurrency,
        use_cache=not args.no_cache,
        threshold=args.threshold,
        label=args.label,
    )
    out_dir, summary = run(cfg, cases)
    print((out_dir / "report.md").read_text(encoding="utf-8").split("## By task")[0].rstrip())
    print(f"\nreport: {out_dir / 'report.md'}")
    if args.github_summary:
        with Path(args.github_summary).open("a", encoding="utf-8") as fh:
            fh.write((out_dir / "report.md").read_text("utf-8"))
    return 0 if summary["passed"] else 1


def cmd_render(args: argparse.Namespace) -> int:
    cases = [c for c in load_cases() if c["id"] == args.case_id]
    if not cases:
        print(f"case {args.case_id!r} not found", file=sys.stderr)
        return 2
    rendered = PromptSet(args.prompt_version).render(cases[0])
    print("=== SYSTEM ===\n" + rendered.system + "\n=== USER ===\n" + rendered.user)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    cases = _filter(load_cases(), args)
    counts: dict[str, int] = {}
    for c in cases:
        k = f"{c['task']}/{c.get('category', 'golden')}"
        counts[k] = counts.get(k, 0) + 1
    print(json.dumps({"total": len(cases), **dict(sorted(counts.items()))}, indent=2))
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    print(compare(Path(args.base), Path(args.new)))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ondetour-eval", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_filters(p: argparse.ArgumentParser) -> None:
        p.add_argument("--task", action="append", choices=["rank", "order", "tips"])
        p.add_argument("--category", action="append", choices=["golden", "edge"])
        p.add_argument("--case", action="append", help="substring of case id (repeatable)")
        p.add_argument("--limit", type=int)

    p = sub.add_parser("run", help="run the suite against a model")
    p.add_argument("--provider", default="claude-cli", choices=["anthropic", "claude-cli", "replay"])
    p.add_argument("--model", default="claude-haiku-5-5")
    p.add_argument("--prompt-version", default="v1")
    p.add_argument("--repeats", type=int, default=1, help="calls per case (measures flakiness)")
    p.add_argument("--concurrency", type=int, default=6)
    p.add_argument("--threshold", type=float, default=0.98)
    p.add_argument("--no-cache", action="store_true", help="ignore cached completions")
    p.add_argument("--replay", help="run dir to replay outputs from (provider=replay)")
    p.add_argument("--dataset", action="append", help="jsonl file(s); default datasets/*.jsonl")
    p.add_argument("--label", help=f"output dir name under {RUNS_DIR.name}/")
    p.add_argument("--github-summary", help="append report.md to this file ($GITHUB_STEP_SUMMARY)")
    add_filters(p)
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("render", help="print the exact prompts for one case")
    p.add_argument("case_id")
    p.add_argument("--prompt-version", default="v1")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("list", help="count cases")
    add_filters(p)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("compare", help="diff two run dirs")
    p.add_argument("base")
    p.add_argument("new")
    p.set_defaults(func=cmd_compare)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
