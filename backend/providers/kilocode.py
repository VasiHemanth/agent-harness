import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base import BaseProvider


class KiloCodeProvider(BaseProvider):
    EXTENSION_ID = "kilocode.kilo-code"

    def __init__(self):
        super().__init__("kilo-code", "KiloCode")
        self.base_dir = self._get_platform_base(
            f"Library/Application Support/Code/User/globalStorage/{self.EXTENSION_ID}",
            f"Code/User/globalStorage/{self.EXTENSION_ID}",
            f"Code/User/globalStorage/{self.EXTENSION_ID}",
        )

    def discover_sessions(self) -> List[Dict[str, Any]]:
        tasks_dir = self.base_dir / "tasks"
        if not tasks_dir.exists():
            return []

        sessions = []
        try:
            for task_id in os.listdir(tasks_dir):
                task_path = tasks_dir / task_id
                if not task_path.is_dir():
                    continue
                ui_path = task_path / "ui_messages.json"
                if not ui_path.exists():
                    continue
                try:
                    mtime = ui_path.stat().st_mtime
                    sessions.append({
                        "id": task_id,
                        "agent": self.name,
                        "project": "KiloCode Task",
                        "timestamp": mtime,
                        "path": str(task_path),
                    })
                except Exception:
                    continue
        except Exception:
            pass

        return sessions

    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        task_path = self.base_dir / "tasks" / session_id
        ui_path = task_path / "ui_messages.json"
        history_path = task_path / "api_conversation_history.json"

        if not ui_path.exists():
            return None

        try:
            with open(ui_path, "r", encoding="utf-8", errors="replace") as f:
                ui_messages = json.load(f)

            model = "kilo-code-auto"
            if history_path.exists():
                try:
                    with open(history_path, "r", encoding="utf-8", errors="replace") as f:
                        history = json.load(f)
                    for msg in history:
                        if msg.get("role") == "user" and isinstance(msg.get("content"), list):
                            for block in msg["content"]:
                                if isinstance(block, dict) and "text" in block:
                                    m = re.search(r"<model>([^<]+)</model>", block["text"])
                                    if m:
                                        raw = m.group(1)
                                        model = raw.split("/")[-1] if "/" in raw else raw
                                        break
                except Exception:
                    pass

            tokens = {"input": 0, "output": 0, "cached": 0, "total": 0, "cost": 0.0}
            for msg in ui_messages:
                if msg.get("type") == "say" and msg.get("say") == "api_req_started" and msg.get("text"):
                    try:
                        data = json.loads(msg["text"])
                        tokens["input"] += data.get("tokensIn", 0)
                        tokens["output"] += data.get("tokensOut", 0)
                        tokens["cached"] += data.get("cacheReads", 0)
                        tokens["cost"] += data.get("cost", 0.0)
                    except Exception:
                        continue

            tokens["total"] = tokens["input"] + tokens["output"]

            return {
                "id": session_id,
                "agent": self.name,
                "model": model,
                "tokens": tokens,
                "timestamp": ui_path.stat().st_mtime,
                "messages_count": len(ui_messages),
            }
        except Exception:
            return None
