import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base import BaseProvider


def _discover_pi_like(sessions_dir: Path, agent_name: str) -> List[Dict[str, Any]]:
    """Shared discovery logic for Pi and OMP (identical JSONL format)."""
    sessions = []
    if not sessions_dir.exists():
        return sessions

    try:
        for project_dir in sessions_dir.iterdir():
            if not project_dir.is_dir():
                continue
            for jsonl_path in project_dir.glob("*.jsonl"):
                if not jsonl_path.is_file():
                    continue
                try:
                    # Read first entry to get session metadata
                    with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
                        first_line = f.readline()
                    if not first_line.strip():
                        continue
                    first = json.loads(first_line)
                    if first.get("type") != "session":
                        continue

                    session_id = first.get("id") or jsonl_path.stem
                    cwd = first.get("cwd") or project_dir.name
                    project = Path(cwd).name if cwd else project_dir.name
                    mtime = jsonl_path.stat().st_mtime

                    sessions.append({
                        "id": session_id,
                        "agent": agent_name,
                        "project": project,
                        "timestamp": mtime,
                        "path": str(jsonl_path),
                    })
                except Exception:
                    continue
    except Exception:
        pass

    return sessions


def _parse_pi_like(session_id: str, jsonl_path: Path, agent_name: str) -> Optional[Dict[str, Any]]:
    """Shared parse logic for Pi and OMP JSONL files."""
    tokens = {"input": 0, "output": 0, "cached": 0, "total": 0, "cost": 0.0}
    model = "gpt-5"

    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue

                if entry.get("type") != "message":
                    continue

                msg = entry.get("message", {})
                if msg.get("role") != "assistant":
                    continue

                usage = msg.get("usage")
                if not usage:
                    continue

                inp = usage.get("input", 0)
                out = usage.get("output", 0)
                cache_read = usage.get("cacheRead", 0)
                cache_write = usage.get("cacheWrite", 0)

                if inp == 0 and out == 0:
                    continue

                m = msg.get("model")
                if m:
                    model = m

                tokens["input"] += inp
                tokens["output"] += out
                tokens["cached"] += cache_read

        tokens["total"] = tokens["input"] + tokens["output"]
    except Exception:
        return None

    return {
        "id": session_id,
        "agent": agent_name,
        "model": model,
        "tokens": tokens,
        "timestamp": jsonl_path.stat().st_mtime,
    }


class PiProvider(BaseProvider):
    def __init__(self):
        super().__init__("pi", "Pi")
        self.sessions_dir = Path.home() / ".pi" / "agent" / "sessions"

    def discover_sessions(self) -> List[Dict[str, Any]]:
        return _discover_pi_like(self.sessions_dir, self.name)

    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        for project_dir in self.sessions_dir.iterdir() if self.sessions_dir.exists() else []:
            if not project_dir.is_dir():
                continue
            for jsonl_path in project_dir.glob("*.jsonl"):
                try:
                    with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
                        first = json.loads(f.readline())
                    if first.get("id") == session_id or jsonl_path.stem == session_id:
                        return _parse_pi_like(session_id, jsonl_path, self.name)
                except Exception:
                    continue
        return None


class OmpProvider(BaseProvider):
    def __init__(self):
        super().__init__("omp", "OMP")
        self.sessions_dir = Path.home() / ".omp" / "agent" / "sessions"

    def discover_sessions(self) -> List[Dict[str, Any]]:
        return _discover_pi_like(self.sessions_dir, self.name)

    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        for project_dir in self.sessions_dir.iterdir() if self.sessions_dir.exists() else []:
            if not project_dir.is_dir():
                continue
            for jsonl_path in project_dir.glob("*.jsonl"):
                try:
                    with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
                        first = json.loads(f.readline())
                    if first.get("id") == session_id or jsonl_path.stem == session_id:
                        return _parse_pi_like(session_id, jsonl_path, self.name)
                except Exception:
                    continue
        return None
