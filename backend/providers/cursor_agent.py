import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from .base import BaseProvider

CHARS_PER_TOKEN = 4
CURSOR_AGENT_COST_MODEL = "claude-sonnet-4-5"

USER_MARKER = re.compile(r"^\s*user:\s*", re.IGNORECASE)
ASSISTANT_MARKER = re.compile(r"^\s*A:\s*")
TOOL_CALL_MARKER = re.compile(r"^\s*\[Tool call\]\s*(.+?)\s*$", re.IGNORECASE)
TOOL_RESULT_MARKER = re.compile(r"^\s*\[Tool result\]\b", re.IGNORECASE)
THINKING_MARKER = re.compile(r"^\s*\[Thinking\]\s*")
USER_QUERY_OPEN = "<user_query>"
USER_QUERY_CLOSE = "</user_query>"
UUID_LIKE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)


def _get_cursor_base() -> Path:
    return Path.home() / ".cursor"


def _extract_user_query(block: str) -> str:
    chunks = []
    cursor = 0
    while cursor < len(block):
        open_idx = block.find(USER_QUERY_OPEN, cursor)
        if open_idx == -1:
            break
        start = open_idx + len(USER_QUERY_OPEN)
        close_idx = block.find(USER_QUERY_CLOSE, start)
        if close_idx == -1:
            chunks.append(block[start:].strip())
            break
        chunks.append(block[start:close_idx].strip())
        cursor = close_idx + len(USER_QUERY_CLOSE)
    combined = " ".join(filter(None, chunks)).strip()
    return combined[:500]


def _parse_text_transcript(content: str):
    """Parse legacy .txt transcript format (user:/A: markers)."""
    turns = []
    active = None
    user_lines = []
    asst_lines = []
    pending_users = []

    def flush_user():
        if not user_lines:
            return
        text = "\n".join(user_lines)
        query = _extract_user_query(text) or text[:500]
        if query:
            pending_users.append(query)
        user_lines.clear()

    def flush_asst():
        if not asst_lines or not pending_users:
            asst_lines.clear()
            return
        body_parts = []
        tools = []
        for line in asst_lines:
            if TOOL_RESULT_MARKER.match(line):
                continue
            tm = TOOL_CALL_MARKER.match(line)
            if tm:
                tools.append(tm.group(1).strip().lower().replace(" ", "-"))
                continue
            if THINKING_MARKER.match(line):
                continue
            body_parts.append(line)
        body = "\n".join(body_parts).strip()
        user_msg = pending_users.pop(0)
        turns.append({"user": user_msg, "output": body, "tools": list(set(tools))})
        asst_lines.clear()

    for line in content.splitlines():
        if USER_MARKER.match(line):
            if active == "user":
                flush_user()
            elif active == "asst":
                flush_asst()
            active = "user"
            user_lines.append(USER_MARKER.sub("", line))
        elif ASSISTANT_MARKER.match(line):
            if active == "user":
                flush_user()
            elif active == "asst":
                flush_asst()
            active = "asst"
            asst_lines.append(ASSISTANT_MARKER.sub("", line))
        elif active == "user":
            user_lines.append(line)
        elif active == "asst":
            asst_lines.append(line)

    if active == "user":
        flush_user()
    if active == "asst":
        flush_asst()

    return turns


def _parse_jsonl_transcript(content: str):
    """Parse newer JSONL transcript format."""
    turns = []
    current_user = ""
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except Exception:
            continue
        if entry.get("role") == "user":
            texts = [b.get("text", "") for b in entry.get("message", {}).get("content", []) if b.get("type") == "text"]
            combined = " ".join(texts)
            current_user = _extract_user_query(combined) or combined[:500]
        elif entry.get("role") == "assistant" and current_user:
            content_blocks = entry.get("message", {}).get("content", [])
            body_parts = [b.get("text", "") for b in content_blocks if b.get("type") == "text"]
            tools = [b.get("name", "").lower() for b in content_blocks if b.get("type") == "tool_use" and b.get("name")]
            turns.append({"user": current_user, "output": "\n".join(body_parts).strip(), "tools": tools})
            current_user = ""
    return turns


class CursorAgentProvider(BaseProvider):
    def __init__(self):
        super().__init__("cursor-agent", "Cursor Agent")
        self.base_dir = _get_cursor_base()
        self.projects_dir = self.base_dir / "projects"

    def _prettify_project_id(self, raw: str) -> str:
        if not raw:
            return raw
        without_prefix = re.sub(r"^-Users-", "", raw)
        parts = [p for p in without_prefix.split("-") if p]
        if parts:
            return parts[-1]
        return raw

    def _discover_transcript_files(self) -> List[Dict[str, Any]]:
        sources = []
        if not self.projects_dir.exists():
            return sources

        try:
            for entry in os.scandir(self.projects_dir):
                if not entry.is_dir():
                    continue
                project = self._prettify_project_id(entry.name)
                transcripts_dir = Path(entry.path) / "agent-transcripts"
                if not transcripts_dir.exists():
                    continue

                try:
                    for t in os.scandir(transcripts_dir):
                        # Legacy: .txt files directly in agent-transcripts/
                        if t.is_file() and (t.name.endswith(".txt") or t.name.endswith(".jsonl")):
                            sources.append({"path": t.path, "project": project, "fmt": "auto"})
                            continue

                        # Composer 2: UUID subdirectory
                        if t.is_dir() and UUID_LIKE.match(t.name):
                            try:
                                for sub in os.scandir(t.path):
                                    if sub.is_file() and (sub.name.endswith(".jsonl") or sub.name.endswith(".txt")):
                                        sources.append({"path": sub.path, "project": project, "fmt": "auto"})
                                    elif sub.is_dir() and sub.name == "subagents":
                                        try:
                                            for sa in os.scandir(sub.path):
                                                if sa.is_file() and (sa.name.endswith(".jsonl") or sa.name.endswith(".txt")):
                                                    sources.append({"path": sa.path, "project": project, "fmt": "auto"})
                                        except Exception:
                                            pass
                            except Exception:
                                pass
                except Exception:
                    continue
        except Exception:
            pass

        return sources

    def discover_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        for src in self._discover_transcript_files():
            path = Path(src["path"])
            stem = path.stem
            session_id = stem if UUID_LIKE.match(stem) else f"cursor-agent-{hash(src['path']) & 0xFFFFFFFF:08x}"
            try:
                mtime = path.stat().st_mtime
                sessions.append({
                    "id": session_id,
                    "agent": self.name,
                    "project": src["project"],
                    "timestamp": mtime,
                    "path": src["path"],
                })
            except Exception:
                continue
        return sessions

    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        for sess in self.discover_sessions():
            if sess["id"] == session_id:
                return self._parse_transcript(session_id, Path(sess["path"]))
        return None

    def _parse_transcript(self, session_id: str, path: Path) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            if path.suffix == ".jsonl":
                turns = _parse_jsonl_transcript(content)
            else:
                turns = _parse_text_transcript(content)

            if not turns:
                return None

            total_input = sum(-(-len(t["user"]) // CHARS_PER_TOKEN) for t in turns)
            total_output = sum(-(-len(t["output"]) // CHARS_PER_TOKEN) for t in turns)

            return {
                "id": session_id,
                "agent": self.name,
                "model": "cursor-agent-auto",
                "tokens": {
                    "input": total_input,
                    "output": total_output,
                    "cached": 0,
                    "total": total_input + total_output,
                    "cost": 0.0,
                },
                "timestamp": path.stat().st_mtime,
            }
        except Exception:
            return None
