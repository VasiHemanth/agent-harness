import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base import BaseProvider

class DroidProvider(BaseProvider):
    def __init__(self):
        super().__init__("droid", "Droid")
        self.base_dir = Path.home() / ".factory"

    def discover_sessions(self) -> List[Dict[str, Any]]:
        sessions_dir = self.base_dir / "sessions"
        if not sessions_dir.exists():
            return []

        sessions = []
        try:
            for sub_dir_name in os.listdir(sessions_dir):
                sub_dir = sessions_dir / sub_dir_name
                if not sub_dir.is_dir():
                    continue
                
                for file_name in os.listdir(sub_dir):
                    if not file_name.endswith(".jsonl"):
                        continue
                    
                    jsonl_path = sub_dir / file_name
                    # Read first line to get session start info
                    with open(jsonl_path, 'r') as f:
                        first_line = f.readline()
                        if not first_line: continue
                        data = json.loads(first_line)
                        if data.get('type') != 'session_start': continue
                        
                        cwd = data.get('cwd', sub_dir_name)
                        if cwd == str(self.base_dir): continue # Skip internal housekeeping

                        sessions.append({
                            "id": f"{sub_dir_name}:{file_name}",
                            "agent": self.name,
                            "project": cwd.split('/')[-1] if '/' in cwd else cwd,
                            "timestamp": jsonl_path.stat().st_mtime,
                            "path": str(jsonl_path)
                        })
        except Exception:
            pass
            
        return sessions

    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            sub_dir_name, file_name = session_id.split(':')
            jsonl_path = self.base_dir / "sessions" / sub_dir_name / file_name
            settings_path = jsonl_path.with_suffix('.settings.json')

            if not jsonl_path.exists():
                return None

            model = "unknown"
            tokens = {"input": 0, "output": 0, "cached": 0, "total": 0, "cost": 0.0}

            if settings_path.exists():
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                    model = settings.get('model', 'unknown')
                    usage = settings.get('tokenUsage', {})
                    tokens["input"] = usage.get('inputTokens', 0)
                    tokens["output"] = usage.get('outputTokens', 0)
                    tokens["cached"] = usage.get('cacheReadTokens', 0)
                    # Reasoning/thinking tokens are often part of output or separate
                    reasoning = usage.get('thinkingTokens', 0)
                    tokens["output"] += reasoning
                    tokens["total"] = tokens["input"] + tokens["output"]

            return {
                "id": session_id,
                "agent": self.name,
                "model": model,
                "tokens": tokens,
                "timestamp": jsonl_path.stat().st_mtime
            }
        except Exception:
            return None
