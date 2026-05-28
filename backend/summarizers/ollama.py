"""Ollama summarizer adapter.

``ollama run <model>`` reads the prompt from stdin and prints plain text. The
model can be supplied to the constructor; otherwise we default to the first
entry from ``ollama list``. Ollama does not write agent-style session traces,
so no cwd-based ingest filter is needed.

Note on timeout: local CPU inference on a 7B+ model can comfortably take 2-5
minutes for a typical trace prompt, so the default here is intentionally much
larger than the cloud-CLI summarizers. Override with TT_OLLAMA_TIMEOUT.
"""
from __future__ import annotations

import os
import re
import subprocess
from typing import Optional

from .base import BaseSummarizer, SummarizerError, run_cli

# Thinking models wrap output in a spinner / ANSI control codes; strip them so
# the downstream JSON parse sees clean text.
_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")

# 6 minutes default — generous enough for an unloaded 13B on Apple Silicon to
# finish a long trace. Override via env if you run something heavier/lighter.
_DEFAULT_TIMEOUT = int(os.environ.get("TT_OLLAMA_TIMEOUT", "360"))


def list_installed_models() -> list[dict]:
    """Return Ollama's installed models, parsed from `ollama list`.

    Each entry: {"name": "llama3:latest", "size": "4.7 GB", "modified": "2 days ago"}.
    Returns [] if Ollama isn't installed or has no models — callers should
    treat that as "show a fallback / no-models hint".
    """
    import shutil
    if not shutil.which("ollama"):
        return []
    try:
        proc = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    lines = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]
    if len(lines) < 2:
        return []
    out: list[dict] = []
    for ln in lines[1:]:  # skip header
        parts = ln.split()
        if not parts:
            continue
        # Format: NAME  ID  SIZE_VAL SIZE_UNIT  MODIFIED…
        name = parts[0]
        size = " ".join(parts[2:4]) if len(parts) >= 4 else ""
        modified = " ".join(parts[4:]) if len(parts) > 4 else ""
        out.append({"name": name, "size": size, "modified": modified})
    return out


class OllamaSummarizer(BaseSummarizer):
    name = "ollama"
    display_name = "Ollama"
    binary = "ollama"

    def __init__(self, model: Optional[str] = None) -> None:
        self._model = model

    def _resolve_model(self) -> str:
        if self._model:
            return self._model
        # First installed model from `ollama list` (skip the header row).
        try:
            proc = subprocess.run(
                [self.binary, "list"],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (OSError, subprocess.SubprocessError) as e:
            raise SummarizerError(f"failed to list ollama models: {e}") from e
        lines = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]
        if len(lines) < 2:
            raise SummarizerError("no ollama models installed")
        model = lines[1].split()[0]
        self._model = model
        return model

    def summarize(self, prompt: str, *, timeout: Optional[int] = None) -> str:
        model = self._resolve_model()
        # Pipe via stdin instead of argv: avoids ARG_MAX limits and shell-
        # special-character pitfalls on big prompts.
        out = run_cli(
            [self.binary, "run", model],
            stdin=prompt,
            timeout=timeout if timeout is not None else _DEFAULT_TIMEOUT,
        )
        return _ANSI_RE.sub("", out).strip()
