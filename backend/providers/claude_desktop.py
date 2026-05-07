import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from .base import BaseProvider


class ClaudeDesktopProvider(BaseProvider):
    def __init__(self):
        super().__init__("claude-desktop", "Claude Desktop")
        if sys.platform == "darwin":
            self.base_dir = Path.home() / "Library/Application Support/Claude/local-agent-mode-sessions"
        elif sys.platform == "win32":
            self.base_dir = Path.home() / "AppData/Roaming/Claude/local-agent-mode-sessions"
        else:
            self.base_dir = Path.home() / ".config/Claude/local-agent-mode-sessions"

    def _walk_jsonl_files(self) -> List[Path]:
        """Recursively find all .jsonl files under the base dir."""
        results = []
        if not self.base_dir.exists():
            return results
        try:
            for root, dirs, files in os.walk(self.base_dir):
                dirs[:] = [d for d in dirs if d not in ("node_modules", ".git")]
                for f in files:
                    if f.endswith(".jsonl"):
                        results.append(Path(root) / f)
        except Exception:
            pass
        return results

    def discover_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        seen = set()
        for jsonl_path in self._walk_jsonl_files():
            session_id = jsonl_path.stem
            if session_id in seen:
                continue
            seen.add(session_id)
            try:
                mtime = jsonl_path.stat().st_mtime
                project = jsonl_path.parent.name
                sessions.append({
                    "id": session_id,
                    "agent": self.name,
                    "project": project,
                    "timestamp": mtime,
                    "path": str(jsonl_path),
                })
            except Exception:
                continue
        return sessions

    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        for jsonl_path in self._walk_jsonl_files():
            if jsonl_path.stem == session_id:
                return self._parse_session(session_id, jsonl_path)
        return None

    def _parse_session(self, session_id: str, jsonl_path: Path) -> Optional[Dict[str, Any]]:
        tokens = {"input": 0, "output": 0, "cached": 0, "total": 0, "cost": 0.0}
        model = "claude-desktop-auto"
        try:
            with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                    except Exception:
                        continue
                    if data.get("type") == "assistant":
                        msg = data.get("message", {})
                        m = msg.get("model")
                        if m and m != "<synthetic>":
                            model = m
                        usage = msg.get("usage", {})
                        if usage:
                            tokens["input"] += usage.get("input_tokens", 0)
                            tokens["output"] += usage.get("output_tokens", 0)
                            tokens["cached"] += usage.get("cache_read_input_tokens", 0)
            tokens["total"] = tokens["input"] + tokens["output"] + tokens["cached"]
        except Exception:
            return None

        return {
            "id": session_id,
            "agent": self.name,
            "model": model,
            "tokens": tokens,
            "timestamp": jsonl_path.stat().st_mtime,
        }
