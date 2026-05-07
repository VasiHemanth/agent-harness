export type Agent = {
  name: string;
  vendor: string;
  captures: string[];
  logPath: string;
  accent: string;
};

export const AGENTS: Agent[] = [
  { name: "Claude Code",  vendor: "Anthropic",  captures: ["tokens", "traces", "reasoning", "cost", "subagents"], logPath: "~/.claude/projects/",                accent: "text-orange-400" },
  { name: "Codex",        vendor: "OpenAI",     captures: ["tokens", "traces", "reasoning", "cost"],              logPath: "~/.codex/sessions/",                  accent: "text-purple-400" },
  { name: "Gemini CLI",   vendor: "Google",     captures: ["tokens", "traces", "cost"],                           logPath: "~/.gemini/",                          accent: "text-cyan-400" },
  { name: "Antigravity",  vendor: "Google",     captures: ["traces", "artifacts", "screenshots", "browser recs"], logPath: "~/.gemini/antigravity/",              accent: "text-emerald-400" },
  { name: "Qwen",         vendor: "Alibaba",    captures: ["tokens", "traces"],                                   logPath: "~/.qwen/",                            accent: "text-blue-400" },
  { name: "Vibe",         vendor: "Local",      captures: ["tokens", "traces", "model"],                          logPath: "~/.vibe/",                            accent: "text-pink-400" },
  { name: "Cursor",       vendor: "Cursor",     captures: ["tokens", "traces", "plans"],                          logPath: "~/.cursor/ + workspaceStorage/",      accent: "text-blue-300" },
  { name: "GitHub Copilot", vendor: "GitHub",   captures: ["tokens", "traces", "cost"],                           logPath: "VS Code chatSessions/",               accent: "text-indigo-400" },
  { name: "OpenCode",     vendor: "OpenCode",   captures: ["tokens", "traces"],                                   logPath: "~/.local/share/opencode/",            accent: "text-amber-400" },
  { name: "Roo Code",       vendor: "Roo Code",    captures: ["tokens", "traces", "cost"],                           logPath: "VS Code globalStorage/tasks/",              accent: "text-teal-400" },
  { name: "Goose",          vendor: "Block",       captures: ["tokens", "traces", "sqlite"],                         logPath: "~/.local/share/goose/",                     accent: "text-yellow-600" },
  { name: "Droid",          vendor: "Factory",     captures: ["tokens", "traces", "jsonl"],                          logPath: "~/.factory/sessions/",                      accent: "text-red-500" },
  { name: "KiloCode",       vendor: "KiloCode",    captures: ["tokens", "traces", "cost"],                           logPath: "VS Code globalStorage/kilocode.kilo-code/", accent: "text-violet-400" },
  { name: "Claude Desktop", vendor: "Anthropic",   captures: ["tokens", "traces", "model"],                          logPath: "~/Library/Application Support/Claude/",     accent: "text-orange-300" },
  { name: "Kiro",           vendor: "AWS",         captures: ["tokens", "traces"],                                   logPath: "~/Library/Application Support/Kiro/",       accent: "text-sky-400" },
  { name: "Pi",             vendor: "Pi",          captures: ["tokens", "traces", "cost"],                           logPath: "~/.pi/agent/sessions/",                     accent: "text-rose-400" },
  { name: "OMP",            vendor: "OMP",         captures: ["tokens", "traces", "cost"],                           logPath: "~/.omp/agent/sessions/",                    accent: "text-lime-400" },
  { name: "Cursor Agent",   vendor: "Cursor",      captures: ["tokens", "traces"],                                   logPath: "~/.cursor/projects/",                       accent: "text-blue-300" },
];
