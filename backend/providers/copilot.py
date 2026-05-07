import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base import BaseProvider

CHARS_PER_TOKEN = 4


def _get_legacy_session_state_dir() -> Path:
    return Path.home() / ".copilot" / "session-state"


def _get_vscode_workspace_storage_dirs() -> List[Path]:
    home = Path.home()
    if sys.platform == "darwin":
        return [
            home / "Library/Application Support/Code/User/workspaceStorage",
            home / "Library/Application Support/Code - Insiders/User/workspaceStorage",
        ]
    if sys.platform == "win32":
        return [
            home / "AppData/Roaming/Code/User/workspaceStorage",
            home / "AppData/Roaming/Code - Insiders/User/workspaceStorage",
        ]
    return [
        home / ".config/Code/User/workspaceStorage",
        home / ".config/Code - Insiders/User/workspaceStorage",
    ]


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


def _parse_legacy_events(content: str, session_id: str) -> Dict[str, Any]:
    """Parse legacy ~/.copilot/session-state/{id}/events.jsonl format."""
    total_output = 0
    model = ""
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except Exception:
            continue
        if event.get("type") == "session.model_change":
            model = event.get("data", {}).get("newModel", model)
        elif event.get("type") == "assistant.message":
            data = event.get("data", {})
            out = data.get("outputTokens", 0)
            if out > 0:
                total_output += out

    return {
        "model": model or "copilot-auto",
        "output_tokens": total_output,
        "input_tokens": 0,
    }


def _infer_model_from_tool_call_ids(events: List[dict]) -> str:
    """Infer Copilot model from tool call ID prefixes in transcript format."""
    anthropic_count = 0
    openai_count = 0
    for e in events:
        if e.get("type") != "assistant.message":
            continue
        for t in e.get("data", {}).get("toolRequests", []):
            tcid = t.get("toolCallId", "")
            if tcid.startswith(("toolu_bdrk_", "toolu_vrtx_", "tooluse_")):
                anthropic_count += 1
            elif tcid.startswith("call_"):
                openai_count += 1
    if anthropic_count > openai_count:
        return "copilot-anthropic-auto"
    if openai_count > 0:
        return "copilot-openai-auto"
    return "copilot-auto"


def _is_transcript_format(content: str) -> bool:
    first_line = content.split("\n")[0].strip()
    try:
        event = json.loads(first_line)
        return event.get("type") == "session.start" and event.get("data", {}).get("producer") == "copilot-agent"
    except Exception:
        return False


def _parse_transcript_events(content: str, session_id: str) -> Dict[str, Any]:
    """Parse VS Code workspaceStorage transcript format."""
    events = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except Exception:
            continue

    model = _infer_model_from_tool_call_ids(events)
    total_input = 0
    total_output = 0

    for e in events:
        if e.get("type") != "assistant.message":
            continue
        data = e.get("data", {})
        content_text = data.get("content", "")
        reasoning_text = data.get("reasoningText", "")
        out = data.get("outputTokens", 0)
        if out == 0:
            out = -(-len(content_text) // CHARS_PER_TOKEN)
            out += -(-len(reasoning_text) // CHARS_PER_TOKEN)
        total_output += out

    return {
        "model": model,
        "output_tokens": total_output,
        "input_tokens": total_input,
    }


class CopilotProvider(BaseProvider):
    def __init__(self):
        super().__init__("copilot", "GitHub Copilot")
        self.legacy_dir = _get_legacy_session_state_dir()
        self.vscode_dirs = _get_vscode_workspace_storage_dirs()

    def _discover_legacy_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        if not self.legacy_dir.exists():
            return sessions

        try:
            for session_id in os.listdir(self.legacy_dir):
                events_path = self.legacy_dir / session_id / "events.jsonl"
                if not events_path.is_file():
                    continue

                project = session_id
                yaml_path = self.legacy_dir / session_id / "workspace.yaml"
                if yaml_path.exists():
                    try:
                        with open(yaml_path, "r", encoding="utf-8") as f:
                            for line in f:
                                if line.startswith("cwd:"):
                                    cwd = line[4:].strip().strip("'\"").split("#")[0].strip()
                                    if cwd:
                                        project = Path(cwd).name
                                    break
                    except Exception:
                        pass

                sessions.append({
                    "id": f"copilot-legacy-{session_id}",
                    "agent": self.name,
                    "project": project,
                    "timestamp": events_path.stat().st_mtime,
                    "path": str(events_path),
                    "_format": "legacy",
                })
        except Exception:
            pass

        return sessions

    def _discover_vscode_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        for ws_storage_dir in self.vscode_dirs:
            if not ws_storage_dir.exists():
                continue
            try:
                for ws_hash in os.listdir(ws_storage_dir):
                    transcripts_dir = ws_storage_dir / ws_hash / "GitHub.copilot-chat" / "transcripts"
                    if not transcripts_dir.exists():
                        continue
                    project = _read_workspace_project(ws_storage_dir / ws_hash)
                    try:
                        for fname in os.listdir(transcripts_dir):
                            if not fname.endswith(".jsonl"):
                                continue
                            file_path = transcripts_dir / fname
                            if not file_path.is_file():
                                continue
                            session_id = f"copilot-vscode-{ws_hash}-{fname}"
                            sessions.append({
                                "id": session_id,
                                "agent": self.name,
                                "project": project,
                                "timestamp": file_path.stat().st_mtime,
                                "path": str(file_path),
                                "_format": "transcript",
                            })
                    except Exception:
                        continue
            except Exception:
                continue
        return sessions

    def discover_sessions(self) -> List[Dict[str, Any]]:
        return self._discover_legacy_sessions() + self._discover_vscode_sessions()

    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        for sess in self.discover_sessions():
            if sess["id"] == session_id:
                return self._parse_session(sess)
        return None

    def _parse_session(self, sess: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        path = Path(sess["path"])
        fmt = sess.get("_format", "legacy")
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            if fmt == "transcript" or _is_transcript_format(content):
                parsed = _parse_transcript_events(content, sess["id"])
            else:
                parsed = _parse_legacy_events(content, sess["id"])

            tokens = {
                "input": parsed["input_tokens"],
                "output": parsed["output_tokens"],
                "cached": 0,
                "total": parsed["input_tokens"] + parsed["output_tokens"],
                "cost": 0.0,
            }

            return {
                "id": sess["id"],
                "agent": self.name,
                "model": parsed["model"],
                "tokens": tokens,
                "timestamp": path.stat().st_mtime,
            }
        except Exception:
            return None
