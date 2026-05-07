import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base import BaseProvider

CHARS_PER_TOKEN = 4


def _get_kiro_agent_dir() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library/Application Support/Kiro/User/globalStorage/kiro.kiroagent"
    if sys.platform == "win32":
        return home / "AppData/Roaming/Kiro/User/globalStorage/kiro.kiroagent"
    return home / ".config/Kiro/User/globalStorage/kiro.kiroagent"


def _get_kiro_workspace_storage_dir() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library/Application Support/Kiro/User/workspaceStorage"
    if sys.platform == "win32":
        return home / "AppData/Roaming/Kiro/User/workspaceStorage"
    return home / ".config/Kiro/User/workspaceStorage"


def _read_workspace_project(ws_dir: Path) -> str:
    try:
        with open(ws_dir / "workspace.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        folder = data.get("folder", "")
        if folder:
            url = folder.replace("file://", "")
            return Path(url).name
    except Exception:
        pass
    return ws_dir.name


def _extract_tool_names(content: str) -> List[str]:
    tools = []
    for m in re.finditer(r"<tool_use>\s*<name>([^<]+)</name>", content):
        tools.append(m.group(1).strip())
    return tools


def _normalize_model_id(raw: str) -> str:
    return re.sub(r"(\d+)\.(\d+)", r"\1-\2", raw)


class KiroProvider(BaseProvider):
    def __init__(self):
        super().__init__("kiro", "Kiro")
        self.agent_dir = _get_kiro_agent_dir()
        self.ws_storage_dir = _get_kiro_workspace_storage_dir()

    def _resolve_workspace_project(self, ws_hash: str) -> str:
        ws_dir = self.ws_storage_dir / ws_hash
        project = _read_workspace_project(ws_dir)
        if project != ws_hash:
            return project

        # Fall back to workspace-sessions base64 directories
        try:
            sessions_path = self.agent_dir / "workspace-sessions"
            for d in os.listdir(sessions_path):
                import base64
                try:
                    decoded = base64.b64decode(d.rstrip("_") + "==").decode("utf-8", errors="replace")
                    if decoded:
                        return Path(decoded).name
                except Exception:
                    continue
        except Exception:
            pass

        return ws_hash

    def discover_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        if not self.agent_dir.exists():
            return sessions

        try:
            for entry in os.scandir(self.agent_dir):
                if not entry.is_dir() or len(entry.name) != 32:
                    continue
                ws_hash = entry.name
                ws_path = self.agent_dir / ws_hash
                project = self._resolve_workspace_project(ws_hash)

                try:
                    for fname in os.listdir(ws_path):
                        if not fname.endswith(".chat"):
                            continue
                        chat_path = ws_path / fname
                        if not chat_path.is_file():
                            continue
                        try:
                            with open(chat_path, "r", encoding="utf-8", errors="replace") as f:
                                data = json.load(f)
                            meta = data.get("metadata", {})
                            start_time = meta.get("startTime", 0)
                            if start_time < 1_000_000_000_000:
                                continue
                            session_id = meta.get("workflowId") or chat_path.stem
                            sessions.append({
                                "id": session_id,
                                "agent": self.name,
                                "project": project,
                                "timestamp": start_time / 1000.0,
                                "path": str(chat_path),
                            })
                        except Exception:
                            continue
                except Exception:
                    continue
        except Exception:
            pass

        return sessions

    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        for sess in self.discover_sessions():
            if sess["id"] == session_id:
                return self._parse_chat_file(session_id, Path(sess["path"]))
        return None

    def _parse_chat_file(self, session_id: str, chat_path: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(chat_path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)

            chat = data.get("chat", [])
            meta = data.get("metadata", {})

            raw_model = meta.get("modelId", "auto")
            model = _normalize_model_id(raw_model) if raw_model and raw_model != "auto" else "kiro-auto"

            total_output_chars = sum(len(m.get("content", "")) for m in chat if m.get("role") == "bot")
            if total_output_chars == 0:
                return None

            output_tokens = -(-total_output_chars // CHARS_PER_TOKEN)  # ceiling division
            user_msgs = [m for m in chat if m.get("role") == "human" and not m.get("content", "").startswith("<identity>")]
            first_user = user_msgs[0].get("content", "")[:500] if user_msgs else ""
            input_tokens = -(-len(first_user) // CHARS_PER_TOKEN)

            return {
                "id": session_id,
                "agent": self.name,
                "model": model,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "cached": 0,
                    "total": input_tokens + output_tokens,
                    "cost": 0.0,
                },
                "timestamp": meta.get("startTime", chat_path.stat().st_mtime * 1000) / 1000.0,
            }
        except Exception:
            return None
