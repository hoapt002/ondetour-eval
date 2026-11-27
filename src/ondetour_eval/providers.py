"""Model providers.

- `anthropic`: Messages API with the exact payload goroute's ClaudeClient sends
  (model, max_tokens, system, one user message; no temperature). Needs ANTHROPIC_API_KEY. Used in CI.
- `claude-cli`: the locally logged-in Claude Code CLI in print mode with tools, CLAUDE.md, hooks and
  plugins disabled and the system prompt replaced. Handy on a dev machine without an API key.
  It cannot set max_tokens, so a response that would exceed 2500 tokens is not truncated like prod.
- `replay`: returns recorded outputs from a previous run (offline re-grading after a checker change).
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from .prompts import RenderedPrompt

PROD_MAX_TOKENS = 2500


@dataclass
class Completion:
    text: str | None
    error: str | None = None
    latency_s: float = 0.0
    input_tokens: int | None = None
    output_tokens: int | None = None
    model: str | None = None


class Provider(ABC):
    name: str

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def complete(self, prompt: RenderedPrompt, case_id: str) -> Completion: ...

    def complete_with_retry(self, prompt: RenderedPrompt, case_id: str, attempts: int = 3) -> Completion:
        last = Completion(text=None, error="not attempted")
        for attempt in range(attempts):
            last = self.complete(prompt, case_id)
            if last.text is not None:
                return last
            time.sleep(2 * (attempt + 1))
        return last


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, model: str, max_tokens: int = PROD_MAX_TOKENS):
        super().__init__(model)
        import anthropic

        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is not set (use --provider claude-cli locally)")
        self.client = anthropic.Anthropic(max_retries=4)
        self.max_tokens = max_tokens

    def complete(self, prompt: RenderedPrompt, case_id: str) -> Completion:
        start = time.monotonic()
        try:
            msg = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=prompt.system,
                messages=[{"role": "user", "content": prompt.user}],
            )
        except Exception as exc:  # noqa: BLE001 — any provider failure is recorded, not raised
            return Completion(text=None, error=f"{type(exc).__name__}: {exc}"[:500], latency_s=time.monotonic() - start)
        # ClaudeClient takes the first non-blank text block.
        text = next((b.text for b in msg.content if b.type == "text" and b.text and b.text.strip()), None)
        return Completion(
            text=text,
            error=None if text is not None else f"no text block (stop_reason={msg.stop_reason})",
            latency_s=time.monotonic() - start,
            input_tokens=msg.usage.input_tokens,
            output_tokens=msg.usage.output_tokens,
            model=msg.model,
        )


class ClaudeCliProvider(Provider):
    name = "claude-cli"

    def __init__(self, model: str, binary: str = "claude", timeout_s: int = 240):
        super().__init__(model)
        self.binary = binary
        self.timeout_s = timeout_s
        self._cwd = tempfile.mkdtemp(prefix="ondetour-eval-")

    def complete(self, prompt: RenderedPrompt, case_id: str) -> Completion:
        cmd = [
            self.binary,
            "-p",
            "--safe-mode",  # no CLAUDE.md, skills, plugins, hooks, MCP
            "--setting-sources",
            "",
            "--tools",
            "",
            "--no-session-persistence",
            "--model",
            self.model,
            "--system-prompt",
            prompt.system,
            "--output-format",
            "json",
        ]
        env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE_CODE_") and k != "CLAUDECODE"}
        start = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                input=prompt.user,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                cwd=self._cwd,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return Completion(text=None, error=f"timeout after {self.timeout_s}s", latency_s=time.monotonic() - start)
        latency = time.monotonic() - start
        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError:
            return Completion(text=None, error=f"cli exit {proc.returncode}: {proc.stderr[-300:]}", latency_s=latency)
        if envelope.get("is_error"):
            return Completion(text=None, error=f"cli error: {str(envelope.get('result'))[:300]}", latency_s=latency)
        usage = envelope.get("usage") or {}
        models = list((envelope.get("modelUsage") or {}).keys())
        return Completion(
            text=envelope.get("result"),
            latency_s=latency,
            input_tokens=(usage.get("input_tokens") or 0)
            + (usage.get("cache_read_input_tokens") or 0)
            + (usage.get("cache_creation_input_tokens") or 0),
            output_tokens=usage.get("output_tokens"),
            model=models[0] if models else None,
        )


class ReplayProvider(Provider):
    name = "replay"

    def __init__(self, model: str, run_dir: Path):
        super().__init__(model)
        self.outputs: dict[str, str | None] = {}
        with (run_dir / "results.jsonl").open(encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                self.outputs[row["key"]] = row["raw"]

    def complete(self, prompt: RenderedPrompt, case_id: str) -> Completion:
        if case_id not in self.outputs:
            return Completion(text=None, error="not in replay run")
        return Completion(text=self.outputs[case_id])

    def complete_with_retry(self, prompt: RenderedPrompt, case_id: str, attempts: int = 1) -> Completion:
        return self.complete(prompt, case_id)


def make_provider(name: str, model: str, replay_dir: Path | None = None) -> Provider:
    if name == "anthropic":
        return AnthropicProvider(model)
    if name == "claude-cli":
        return ClaudeCliProvider(model)
    if name == "replay":
        if replay_dir is None:
            raise ValueError("--replay RUN_DIR is required for the replay provider")
        return ReplayProvider(model, replay_dir)
    raise ValueError(f"unknown provider {name!r}")
