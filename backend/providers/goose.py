import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base import BaseProvider
import json

class GooseProvider(BaseProvider):
    def __init__(self):
        super().__init__("goose", "Goose")
        # goose/sessions/sessions.db
        if os.name == 'nt':
            self.db_path = Path.home() / "AppData/Roaming/Block/goose/sessions/sessions.db"
        else:
            # Check XDG_DATA_HOME
            xdg_data = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share"))
            self.db_path = Path(xdg_data) / "goose/sessions/sessions.db"

    def discover_sessions(self) -> List[Dict[str, Any]]:
        if not self.db_path.exists():
            return []

        sessions = []
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query sessions table
            query = """
            SELECT id, name, working_dir, updated_at, created_at, 
                   accumulated_input_tokens, accumulated_output_tokens 
            FROM sessions 
            ORDER BY updated_at DESC
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            
            for row in rows:
                if (row['accumulated_input_tokens'] or 0) == 0 and (row['accumulated_output_tokens'] or 0) == 0:
                    continue
                
                # Format timestamp
                ts_str = row['updated_at'] or row['created_at']
                import datetime
                try:
                    ts = datetime.datetime.fromisoformat(ts_str.replace('Z', '+00:00')).timestamp()
                except:
                    ts = datetime.datetime.now().timestamp()

                sessions.append({
                    "id": row['id'],
                    "agent": self.name,
                    "project": row['working_dir'].split('/')[-1] if row['working_dir'] else "Goose",
                    "timestamp": ts,
                    "tokens_preview": {
                        "input": row['accumulated_input_tokens'] or 0,
                        "output": row['accumulated_output_tokens'] or 0
                    }
                })
            conn.close()
        except Exception as e:
            print(f"Error discovering Goose sessions: {e}")
            
        return sessions

    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not self.db_path.exists():
            return None

        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            session_row = cursor.fetchone()
            if not session_row:
                conn.close()
                return None

            # Get model info
            model = "unknown"
            if session_row['model_config_json']:
                try:
                    config = json.loads(session_row['model_config_json'])
                    model = config.get('model_name', 'unknown')
                except: pass

            tokens = {
                "input": session_row['accumulated_input_tokens'] or 0,
                "output": session_row['accumulated_output_tokens'] or 0,
                "cached": 0,
                "total": (session_row['accumulated_input_tokens'] or 0) + (session_row['accumulated_output_tokens'] or 0),
                "cost": 0.0 # Will be calculated by frontend or central pricing logic
            }

            conn.close()
            return {
                "id": session_id,
                "agent": self.name,
                "model": model,
                "tokens": tokens,
                "project": session_row['working_dir'],
                "timestamp": session_row['updated_at']
            }
        except Exception:
            return None
