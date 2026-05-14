"""
Custom-agent log adapter.

Reads ~/.tokentelemetry/custom-agents.json (optional) and produces normalized
sessions from arbitrary JSONL log files. Designed for "coworker" proxies that
delegate Claude Code traffic to cheaper backends (deepclaude, claude-coworker-model,
triss, etc.) so their cost can appear side-by-side in the dashboard.

Config schema — a JSON array of entries:
[
  {
    "name": "deepclaude",                       // agent key (used in /agents)
    "log_glob": "~/.deepclaude/agent-*.jsonl",  // expanded with ~ + globs
    "fields": {                                 // map JSONL keys → canonical fields
      "session_id":    "agentId",               // dot-paths supported (a.b.c)
      "timestamp":     "ts",                    // ISO8601, unix s, or unix ms
      "model":         "model",
      "input_tokens":  "usage.input_tokens",
      "output_tokens": "usage.output_tokens",
      "cached_tokens": "usage.cached_tokens",   // optional
      "project":       "cwd",                   // optional
      "display":       "prompt"                 // optional
    },
    "default_model": "deepseek-v4-pro",         // fallback when model missing

    // Optional UI overrides (frontend auto-picks distinct defaults otherwise):
    "label": "DeepClaude",
    "color": "#8b5cf6",                         // any CSS hex
    "icon":  "puzzle"                           // lucide icon name (lowercase)
  }
]
"""

import json
import os
from datetime import datetime, timezone
from glob import glob
from pathlib import Path
from typing import Callable, Dict, List, Optional

HOME = Path.home()
CUSTOM_AGENTS_CONFIG = HOME / ".tokentelemetry" / "custom-agents.json"


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _get_path(obj, path: Optional[str]):
    if not path or obj is None:
        return None
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
        if cur is None:
            return None
    return cur


def _parse_ts(raw) -> datetime:
    if raw is None:
        return _now()
    if isinstance(raw, bool):
        return _now()
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw / 1000 if raw > 1e12 else raw, tz=timezone.utc)
    if isinstance(raw, str):
        try:
            return _aware(datetime.fromisoformat(raw.replace("Z", "+00:00")))
        except Exception:
            pass
    return _now()


def _expand_glob(pattern: str) -> List[str]:
    return glob(os.path.expanduser(pattern))


def load_custom_agent_configs() -> List[Dict]:
    if not CUSTOM_AGENTS_CONFIG.exists():
        return []
    try:
        data = json.loads(CUSTOM_AGENTS_CONFIG.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [c for c in data if isinstance(c, dict) and c.get("name") and c.get("log_glob")]
    except Exception:
        pass
    return []


def get_available_custom_agents() -> List[str]:
    out = []
    for cfg in load_custom_agent_configs():
        if _expand_glob(cfg["log_glob"]):
            out.append(cfg["name"])
    return out


def get_custom_agent_meta() -> List[Dict]:
    """UI overrides per custom agent. Frontend fills in defaults for missing fields."""
    out = []
    for cfg in load_custom_agent_configs():
        entry = {"name": cfg["name"]}
        for key in ("label", "color", "icon"):
            if cfg.get(key):
                entry[key] = cfg[key]
        out.append(entry)
    return out


def scan_custom_agents(
    apply_alias: Callable[[str], str],
    calculate_cost: Callable[[Optional[str], int, int, int], float],
) -> List[Dict]:
    """Return a list of session dicts matching the shape used in main._scan_sessions_sync()."""
    out: List[Dict] = []
    for cfg in load_custom_agent_configs():
        name = cfg["name"]
        fields = cfg.get("fields", {}) or {}
        default_model = cfg.get("default_model")
        sessions: Dict[str, Dict] = {}

        for path_str in _expand_glob(cfg["log_glob"]):
            path = Path(path_str)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            row = json.loads(line)
                        except Exception:
                            continue
                        if not isinstance(row, dict):
                            continue

                        sid = _get_path(row, fields.get("session_id")) or path.stem
                        sid = str(sid)
                        ts = _parse_ts(_get_path(row, fields.get("timestamp")))
                        model = _get_path(row, fields.get("model")) or default_model
                        in_tok = int(_get_path(row, fields.get("input_tokens")) or 0)
                        out_tok = int(_get_path(row, fields.get("output_tokens")) or 0)
                        cached_tok = int(_get_path(row, fields.get("cached_tokens")) or 0)
                        project_raw = _get_path(row, fields.get("project")) or "unknown"
                        project = apply_alias(str(project_raw))
                        display = _get_path(row, fields.get("display"))

                        if sid not in sessions:
                            sessions[sid] = {
                                "id": sid,
                                "agent": name,
                                "project": project,
                                "timestamp": ts,
                                "display": display,
                                "tokens": {"input": 0, "output": 0, "cached": 0, "total": 0},
                                "mcp_tools": [],
                                "has_plan": False,
                                "plans": [],
                                "model": model,
                                "artifacts": [],
                            }
                        s = sessions[sid]
                        s["tokens"]["input"] += in_tok
                        s["tokens"]["output"] += out_tok
                        s["tokens"]["cached"] += cached_tok
                        s["tokens"]["total"] = (
                            s["tokens"]["input"] + s["tokens"]["output"] + s["tokens"]["cached"]
                        )
                        if ts > s["timestamp"]:
                            s["timestamp"] = ts
                        if model and not s.get("model"):
                            s["model"] = model
                        s["cost"] = calculate_cost(
                            s.get("model"),
                            s["tokens"]["input"],
                            s["tokens"]["output"],
                            s["tokens"]["cached"],
                        )
            except Exception:
                continue

        out.extend(sessions.values())
    return out
