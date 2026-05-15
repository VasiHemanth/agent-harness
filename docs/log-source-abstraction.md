# LogSource Abstraction — Design Note

## Problem

`backend/main.py:_scan_sessions_sync()` is now ~650 lines of per-agent parser blocks. Each new agent (and now: each new coworker proxy like deepclaude/triss) bolts on another block. The shape of those blocks is nearly identical — find files, read JSONL, extract a handful of fields, normalize, emit a `Session`. The current `custom_agents.py` adapter (this branch) proves the pattern works for arbitrary third-party JSONL; the built-in agents should converge on the same contract.

## Goals

1. One contract every parser implements. No special-casing in the scan loop.
2. Adding a new agent = adding one file (or one config entry), no edits to `main.py`.
3. Users can register their own log sources via config, without forking.
4. Backwards-compatible — existing `Session` shape and API responses stay identical.

## Non-goals

- A streaming pipeline (OpenTelemetry-scale). We scan on demand behind a TTL cache; that's enough.
- Auto-format detection. Users declare the format in config. Detection magic is where these abstractions usually rot.
- Text-log parsing. JSON / JSONL only for v1.

## Shape

### `LogSource` interface

```python
class LogSource(Protocol):
    name: str                          # "claude", "codex", "deepclaude", ...
    label: str                         # human-readable, defaults to name.title()

    def is_available(self) -> bool:    # cheap existence check (dir exists, etc.)
        ...

    def scan(self, ctx: ScanContext) -> list[NormalizedSession]:
        ...
```

`ScanContext` carries the bits parsers need (alias resolver, pricing fn, project-hide list).

### `NormalizedSession` (the contract)

Identical to today's `Session` model plus `cost: float` and optional `model: str`. Already enforced by Pydantic; we just need every parser to populate it consistently.

### Registry

```python
_BUILTIN_SOURCES: list[LogSource] = [
    ClaudeSource(), CodexSource(), GeminiSource(),
    AntigravitySource(), QwenSource(), VibeSource(),
    CursorSource(), CopilotSource(), OpencodeSource(),
]

def all_sources() -> list[LogSource]:
    return _BUILTIN_SOURCES + load_custom_sources()
```

`load_custom_sources()` returns `JsonlLogSource` instances built from `~/.tokentelemetry/custom-agents.json` — the format we just shipped on this branch.

`_scan_sessions_sync()` collapses to:

```python
def _scan_sessions_sync():
    ctx = ScanContext(...)
    sessions = []
    for source in all_sources():
        if not source.is_available():
            continue
        try:
            sessions.extend(source.scan(ctx))
        except Exception:
            log.exception("scan failed: %s", source.name)
    sessions.sort(key=lambda s: s["timestamp"], reverse=True)
    return sessions
```

`/agents` collapses to `[s.name for s in all_sources() if s.is_available()]`.

## Custom-source config (already shipped on this branch)

`~/.tokentelemetry/custom-agents.json`:

```json
[
  {
    "name": "deepclaude",
    "log_glob": "~/.deepclaude/agent-*.jsonl",
    "fields": {
      "session_id":    "agentId",
      "timestamp":     "ts",
      "model":         "model",
      "input_tokens":  "usage.input_tokens",
      "output_tokens": "usage.output_tokens",
      "cached_tokens": "usage.cached_tokens",
      "project":       "cwd",
      "display":       "prompt"
    },
    "default_model": "deepseek-v4-pro"
  }
]
```

Dot-paths for nested fields. Timestamps: ISO8601 / unix s / unix ms (auto). Cost via existing `pricing.calculate_cost()`.

## Migration plan

This is a refactor, not a rewrite. Do it incrementally — one parser per PR — so it stays reviewable and never breaks the live dashboard.

1. **This branch (already done):** Ship `custom_agents.py` + pricing additions. Establishes the "third-party JSONL" contract that the abstraction will generalize.
2. **PR A:** Add `LogSource` Protocol, `ScanContext`, and `JsonlLogSource` (lifted from `custom_agents.py`). No built-ins moved yet. Replace the custom-agents call site to go through the new registry.
3. **PR B–J:** One PR per built-in. Move Claude → `sources/claude.py`. Run, compare API responses against a fixture. Repeat for Codex, Gemini, Antigravity, Cursor, Copilot, Qwen, Vibe, OpenCode.
4. **PR K:** Delete `_scan_sessions_sync` once it's empty; rename the replacement to `scan_all_sources()`.

Acceptance per PR: `/sessions`, `/projects`, `/analytics` response shape is byte-identical to pre-refactor for a known fixture set.

## Risks

- **Parser quirks won't all fit the protocol cleanly.** Cursor's subagent extraction, Claude's plan-snippet harvesting, OpenCode's SQLite path. Solution: the Protocol stays narrow (`scan() → list[Session]`); each source can keep arbitrary internal helpers.
- **Custom-source breakage is silent today** — bad config = no rows shown, no error. Add a `GET /agents/diagnostics` endpoint that returns per-source `{available, scanned_files, last_error}`. Defer to PR A.
- **Plugin security.** Config-driven JSONL adapters are inert (no code execution). If we later add Python plugins, gate them behind an explicit `--allow-plugins` flag.

## What this unlocks

- DeepSeek/Kimi/Qwen coworker-proxy costs side-by-side with Claude (the original reddit ask).
- In-house agents at companies that don't want to upstream parsers.
- A clean place to add streaming/tailing later, if real-time becomes a need.

## Future: parent-call grouping

Some coworker proxies emit a `parent_call_id` on each record (e.g., Triss
populates it when the host exports `TRISS_PARENT_CALL_ID` in the MCP env
block). The natural extension: add an optional `parent_session_id` field
to the mapping, and let the dashboard render a "rolled-up" view that
groups every child call under its outer Claude session. Mechanically
small; the UX question is the harder part (drill-down vs. inline child
rows). Defer until two real sources need it.
