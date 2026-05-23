"""TokenTelemetry config: aliases + hidden projects.

Lives at ~/.tokentelemetry/. Three files:
  - aliases.json   {"/old/path": "/new/path", ...}   one-way, no chains
  - hidden.json    ["/path", ...]                    projects excluded from dashboard
  - VERSION        single integer for future migrations

Design rules:
  - Dir is created lazily on first write, never on read.
  - Writes are atomic (tmp + rename). A crash mid-write won't corrupt config.
  - Reads never raise; missing/malformed files return empty defaults.
  - Aliases are applied at read time only. Log files are never modified.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Set

HARNESS_DIR = Path.home() / ".tokentelemetry"
ALIASES_FILE = HARNESS_DIR / "aliases.json"
HIDDEN_FILE = HARNESS_DIR / "hidden.json"
VERSION_FILE = HARNESS_DIR / "VERSION"
SCHEMA_VERSION = 1


def _ensure_dir() -> None:
    HARNESS_DIR.mkdir(parents=True, exist_ok=True)
    if not VERSION_FILE.exists():
        VERSION_FILE.write_text(str(SCHEMA_VERSION))


def _atomic_write_json(path: Path, data) -> None:
    """Write JSON atomically. Crash during write can't corrupt the existing file."""
    _ensure_dir()
    fd, tmp = tempfile.mkstemp(dir=str(HARNESS_DIR), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
    except Exception:
        try: os.unlink(tmp)
        except Exception: pass
        raise


def load_aliases() -> Dict[str, str]:
    """Return old-path -> new-path map. One-way, no chains resolved.

    Invalid entries (non-string, self-referencing, chained) are skipped silently.
    """
    if not ALIASES_FILE.exists():
        return {}
    try:
        with open(ALIASES_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, str] = {}
    for k, v in raw.items():
        if not isinstance(k, str) or not isinstance(v, str): continue
        if not k or not v or k == v: continue
        # Reject chains: if v is itself a key, this alias is ambiguous.
        if v in raw: continue
        out[k] = v
    return out


def apply_alias(path: str, aliases: Dict[str, str]) -> str:
    """One-way, non-recursive lookup. Returns path unchanged if not aliased."""
    return aliases.get(path, path)


def load_hidden() -> Set[str]:
    """Return the set of project paths the user has chosen to hide."""
    if not HIDDEN_FILE.exists():
        return set()
    try:
        with open(HIDDEN_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return set()
    if not isinstance(raw, list):
        return set()
    return {p for p in raw if isinstance(p, str) and p}


def save_hidden(paths: Set[str]) -> None:
    _atomic_write_json(HIDDEN_FILE, sorted(paths))


def hide_project(path: str) -> Set[str]:
    current = load_hidden()
    current.add(path)
    save_hidden(current)
    return current


def unhide_project(path: str) -> Set[str]:
    current = load_hidden()
    current.discard(path)
    save_hidden(current)
    return current


def list_aliases() -> Dict[str, str]:
    return load_aliases()


def save_aliases(aliases: Dict[str, str]) -> None:
    """Overwrite the alias file. Caller is responsible for validation."""
    _atomic_write_json(ALIASES_FILE, aliases)
