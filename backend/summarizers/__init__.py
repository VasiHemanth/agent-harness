"""Summarizer backend registry.

Adapters register here. Only adapters whose CLI is installed are offered to the
frontend, so the onboarding picker shows exactly what the user can actually run.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .base import BaseSummarizer, SummarizerError
from .claude import ClaudeSummarizer
from .codex import CodexSummarizer
from .gemini import GeminiSummarizer
from .antigravity import AntigravitySummarizer
from .ollama import OllamaSummarizer
from .qwen import QwenSummarizer

# Only adapters whose CLI is installed are offered to the frontend.
_ALL: List[BaseSummarizer] = [
    ClaudeSummarizer(),
    CodexSummarizer(),
    GeminiSummarizer(),
    AntigravitySummarizer(),
    QwenSummarizer(),
    OllamaSummarizer(),
]

_BY_NAME: Dict[str, BaseSummarizer] = {s.name: s for s in _ALL}


def get_summarizer(name: str, model: Optional[str] = None) -> Optional[BaseSummarizer]:
    """Look up a backend by name. For Ollama, if ``model`` is given, return a
    fresh instance bound to that model rather than the registry singleton
    (which auto-picks the first installed model)."""
    if name == "ollama" and model:
        return OllamaSummarizer(model=model)
    return _BY_NAME.get(name)


def available_summarizers() -> List[BaseSummarizer]:
    """Installed, runnable backends — what onboarding should offer."""
    return [s for s in _ALL if s.is_available()]


__all__ = [
    "BaseSummarizer",
    "SummarizerError",
    "get_summarizer",
    "available_summarizers",
]
