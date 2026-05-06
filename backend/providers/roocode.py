import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base import BaseProvider
import os

class RooCodeProvider(BaseProvider):
    EXTENSION_ID = "rooveterinaryinc.roo-cline"

    def __init__(self):
        super().__init__("roo-code", "Roo Code")
        self.base_dir = self._get_platform_base(
            f"Library/Application Support/Code/User/globalStorage/{self.EXTENSION_ID}",
            f"Code/User/globalStorage/{self.EXTENSION_ID}",
            f"Code/User/globalStorage/{self.EXTENSION_ID}"
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

                ui_messages_path = task_path / "ui_messages.json"
                if not ui_messages_path.exists():
                    continue

                # Get modification time for timestamp
                mtime = ui_messages_path.stat().st_mtime
                
                # Basic metadata for now, full parsing in get_session_details
                sessions.append({
                    "id": task_id,
                    "agent": self.name,
                    "project": "Roo Code Task", # Cline/Roo doesn't always have a clear project name in task folder
                    "timestamp": mtime,
                    "path": str(task_path)
                })
        except Exception:
            pass
            
        return sessions

    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        task_path = self.base_dir / "tasks" / session_id
        ui_messages_path = task_path / "ui_messages.json"
        history_path = task_path / "api_conversation_history.json"

        if not ui_messages_path.exists():
            return None

        try:
            with open(ui_messages_path, 'r') as f:
                ui_messages = json.load(f)
            
            model = "roo-auto"
            if history_path.exists():
                with open(history_path, 'r') as f:
                    history = json.load(f)
                    # Extract model from history content if possible (similar to reference)
                    for msg in history:
                        if msg.get('role') == 'user' and isinstance(msg.get('content'), list):
                            for block in msg['content']:
                                if isinstance(block, dict) and 'text' in block:
                                    import re
                                    match = re.search(r"<model>([^<]+)</model>", block['text'])
                                    if match:
                                        model = match.group(1).split('/')[-1]
                                        break

            total_tokens = {"input": 0, "output": 0, "cached": 0, "total": 0, "cost": 0.0}
            messages = []
            
            # Extract token usage from api_req_started events
            for msg in ui_messages:
                if msg.get('type') == 'say' and msg.get('say') == 'api_req_started' and msg.get('text'):
                    try:
                        data = json.loads(msg['text'])
                        t_in = data.get('tokensIn', 0)
                        t_out = data.get('tokensOut', 0)
                        c_read = data.get('cacheReads', 0)
                        cost = data.get('cost', 0.0)
                        
                        total_tokens["input"] += t_in
                        total_tokens["output"] += t_out
                        total_tokens["cached"] += c_read
                        total_tokens["cost"] += cost
                    except:
                        continue

            total_tokens["total"] = total_tokens["input"] + total_tokens["output"]

            return {
                "id": session_id,
                "agent": self.name,
                "model": model,
                "tokens": total_tokens,
                "timestamp": ui_messages_path.stat().st_mtime,
                "messages_count": len(ui_messages)
            }
        except Exception:
            return None
