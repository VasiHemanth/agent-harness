# Missing Features — Gap Analysis vs codeburn-reference

Features present in `codeburn-reference` that are not yet in the current codebase.

---

## 1. Task Categorization + One-Shot Rate

**Priority: High** — infrastructure already partially wired, stubs exist but commented out

- Deterministic classifier assigns each session turn to one of 13 task categories:
  - Coding, Debugging, Feature Dev, Refactoring, Testing, Exploration, Planning, Delegation, Git Ops, Build/Deploy, Conversation, Brainstorming, General
- Classification uses tool patterns + keyword matching (no LLM calls)
- **One-shot rate**: detects edit→bash→edit retry cycles, tracks % of edits that succeed on first try
- Per-category one-shot rates surfaced in analytics
- Self-correction rate: detects when the model is fixing its own earlier mistakes
- Delegation rate: tracks how often subagents are spawned

---

## 2. Tool / MCP / Bash Breakdown on Analytics Page

**Priority: High** — data already in sessions, needs aggregation + UI

- Per-tool call counts and cost share (Read, Edit, Write, Bash, Agent, etc.)
- Per-MCP-server usage stats
- Bash/shell command breakdown (which commands are run most)
- All three surfaced as panels on the analytics page

---

## 3. Pricing Accuracy Improvements

**Priority: High** — affects cost correctness for all users

- **Fast mode multiplier**: 6x cost for Claude Opus fast mode sessions
- **Reasoning token tracking**: separate accounting for thinking/reasoning tokens (o1-style models)
- **Web search request cost**: tracks web search tool usage and bills it separately
- **Model aliases**: map proxy/custom model names → canonical names for correct pricing lookup

---

## 4. Optimize / Waste Detection Engine

**Priority: Medium** — new backend endpoint + new frontend page

Backend scans for waste patterns and returns findings with health grade A–F:

| Finding | Detection Logic | Impact |
|---|---|---|
| CLAUDE.md bloat | File size + @-import expansion; threshold 400+ lines high, 200+ medium | High |
| Duplicate reads | Content-hash matching across sessions; 30+ high, 10+ medium | High |
| Low read:edit ratio | Editing without reading leads to retries; healthy 4:1, flag at 2:1 | High |
| Unused MCP servers | Configured but never called; ~2000 tokens per unused server | Medium |
| Ghost agents | Defined in agents/ but never invoked; 5+ high, 2+ medium | Medium |
| Ghost skills | Defined but never invoked; 10+ high, 5+ medium | Medium |
| Ghost commands | Slash commands defined but never used; 10+ medium | Low |
| Cache excess | >15,000 cache creation tokens suggests config issues | Medium |
| Bash bloat | `BASH_MAX_OUTPUT_LENGTH` uncapped (default 30k, recommend 15k) | Low |

Frontend: new `/optimize` page showing findings list with recommended actions and savings estimates.

---

## 5. Context Budget Estimation

**Priority: Medium** — per-project diagnostic

- Estimates how much context budget a project consumes at startup:
  - MCP tool definitions (~400 tokens each)
  - Skill files (`SKILL.md` per skill)
  - Memory files (`CLAUDE.md`, `AGENTS.md`, etc.)
  - Subagent definitions
- Exposed on the project Config tab

---

## 6. Model Comparison Page

**Priority: Medium** — new frontend page

Side-by-side comparison of any two models across:

**Performance metrics**
- One-shot rate (% edits succeeding first try)
- Retry rate (avg retries per edit)
- Self-correction rate

**Efficiency metrics**
- Cost per call
- Cost per edit
- Output tokens per call
- Cache hit rate

**Working style**
- Tools per turn (avg)
- Delegation rate
- Planning rate
- Fast mode usage rate

**Per-category breakdown**: one-shot rates for Coding, Debugging, Testing, etc.

---

## 7. Additional Agent Providers

**Priority: Medium** — extend the modular provider system

| Provider | Data Location |
|---|---|
| Claude Desktop | `~/Library/Application Support/Claude/local-agent-mode-sessions/` |
| GitHub Copilot | `~/.copilot/session-state/` + VS Code workspaceStorage |
| Kiro | `~/Library/Application Support/Kiro/User/globalStorage/kiro.kiroagent/` |
| KiloCode | VS Code `globalStorage/kilocode.kilo-code/tasks/` (same format as Roo Code) |
| OpenClaw | `~/.openclaw/agents/` JSONL (legacy: `.clawdbot`, `.moltbot`) |
| Pi | `~/.pi/agent/sessions/` JSONL |
| OMP (Oh My Pi) | `~/.omp/agent/sessions/` JSONL |
| Cursor Agent | `~/.cursor/projects/` (separate from Cursor IDE) |

---

## 8. Export (CSV / JSON Download)

**Priority: Medium** — analytics utility

CSV export (multi-sheet):
- Daily breakdown
- Project breakdown
- Model breakdown
- Activity/category breakdown
- Top sessions
- Shell commands

JSON export (structured):
- Full analytics snapshot including overview, daily array, projects, models, activities, tools, MCP servers, shell commands

Frontend: download button on the analytics page.

---

## 9. Budget / Plan Tracking

**Priority: Low–Medium** — subscription management feature

Preset plans:
- Claude Pro — $20/month
- Claude Max 20x — $200/month
- Claude Max 5x — $100/month
- Cursor Pro — $20/month
- Custom — user-defined

Tracks:
- Budget USD vs spent API-equivalent USD
- Percent used, projected month-end cost
- Days until billing reset (configurable reset day 1–28)
- Status: under / near / over

Frontend: progress bar widget on dashboard, dedicated settings page.

---

## 10. Multi-Currency Support

**Priority: Low** — display utility

- 162 ISO 4217 currencies
- Exchange rates from Frankfurter API (ECB data, free, cached 24h)
- All cost displays convert from USD at runtime
- Configurable via settings page

---

## 11. Yield / Git Correlation

**Priority: Low** — requires git integration per project

Categorizes sessions as:
- **Productive** — resulted in commits that landed in main branch
- **Reverted** — commits that were later reverted
- **Abandoned** — no commits or never merged

Correlation window: session timestamp ± 1h vs commit timestamps.

Exposed as a tab or metric on the project detail page.

---

## Implementation Notes

- Items 1–3 are backend-first: add to `backend/main.py` analytics endpoint and session parsing.
- Items 4–5 are new backend endpoints + new frontend pages.
- Item 6 is a new frontend page consuming existing analytics data.
- Item 7 follows the existing modular provider pattern in `backend/providers/`.
- Items 8–11 are self-contained features with clear boundaries.
