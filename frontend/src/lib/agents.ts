import {
  Terminal, Database, Sparkles, Orbit, Cpu, Zap, MousePointer2,
  GitBranch, Code2,
  Puzzle, Workflow, Wand2, Bot, Network, Layers, Box, Cog,
  Rocket, Wrench, Flame, Gem,
  type LucideIcon,
} from "lucide-react";

export type AgentKey =
  | "claude" | "codex" | "gemini" | "antigravity"
  | "qwen" | "vibe" | "cursor" | "copilot" | "opencode";

export interface AgentMeta {
  key: AgentKey | string;
  label: string;
  /** Brand hex, also exposed as `--agent-{key}` CSS variable. */
  hex: string;
  icon: LucideIcon;
  /** True for agents loaded from ~/.tokentelemetry/custom-agents.json. */
  isCustom?: boolean;
}

export const AGENTS: Record<AgentKey, AgentMeta> = {
  claude:      { key: "claude",      label: "Claude Code", hex: "#f97316", icon: Terminal },
  codex:       { key: "codex",       label: "Codex",       hex: "#a855f7", icon: Database },
  gemini:      { key: "gemini",      label: "Gemini CLI",  hex: "#06b6d4", icon: Sparkles },
  antigravity: { key: "antigravity", label: "Antigravity", hex: "#10b981", icon: Orbit },
  qwen:        { key: "qwen",        label: "Qwen CLI",    hex: "#3b82f6", icon: Cpu },
  vibe:        { key: "vibe",        label: "Vibe",        hex: "#f472b6", icon: Zap },
  cursor:      { key: "cursor",      label: "Cursor",      hex: "#60a5fa", icon: MousePointer2 },
  copilot:     { key: "copilot",     label: "Copilot",     hex: "#6366f1", icon: GitBranch },
  opencode:    { key: "opencode",    label: "OpenCode",    hex: "#f59e0b", icon: Code2 },
};

const FALLBACK: AgentMeta = {
  key: "claude", label: "Unknown", hex: "#64748b", icon: Terminal,
};

// ---------------------------------------------------------------------------
// Custom agent registry — populated at app load from /custom-agent-meta.
// Built-in AGENTS stay first-class; customs fall through to here.
// ---------------------------------------------------------------------------

/** Lucide icons available to custom agents via the `icon` field in config. */
const ICON_MAP: Record<string, LucideIcon> = {
  puzzle: Puzzle, workflow: Workflow, wand2: Wand2, bot: Bot, network: Network,
  layers: Layers, box: Box, cog: Cog, rocket: Rocket, wrench: Wrench,
  flame: Flame, gem: Gem,
  // also expose built-in icons so custom agents can pick them
  terminal: Terminal, database: Database, sparkles: Sparkles, orbit: Orbit,
  cpu: Cpu, zap: Zap, code2: Code2, "git-branch": GitBranch,
};

/** Palette + icon pairs used to auto-assign distinct visuals when the user
 *  doesn't specify `color`/`icon` in custom-agents.json. Pre-paired so each
 *  index gives a coherent look. Hues avoid the built-in brand palette. */
const CUSTOM_DEFAULTS: Array<{ hex: string; icon: LucideIcon }> = [
  { hex: "#8b5cf6", icon: Puzzle   }, // violet
  { hex: "#14b8a6", icon: Workflow }, // teal
  { hex: "#f43f5e", icon: Flame    }, // rose
  { hex: "#84cc16", icon: Layers   }, // lime
  { hex: "#d946ef", icon: Wand2    }, // fuchsia
  { hex: "#ef4444", icon: Bot      }, // red
  { hex: "#0891b2", icon: Network  }, // sky
  { hex: "#facc15", icon: Gem      }, // amber
  { hex: "#7c3aed", icon: Rocket   }, // deep purple
  { hex: "#059669", icon: Wrench   }, // deep green
  { hex: "#db2777", icon: Box      }, // hot pink
  { hex: "#ea580c", icon: Cog      }, // burnt orange
];

function hashIndex(name: string, mod: number): number {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = (h * 31 + name.charCodeAt(i)) >>> 0;
  return h % mod;
}

const _customRegistry: Record<string, AgentMeta> = {};

export interface CustomAgentOverride {
  name: string;
  label?: string;
  color?: string;
  icon?: string;
}

/** Hydrates the runtime registry. Called once on app load with whatever the
 *  /custom-agent-meta endpoint returned. Two-pass assignment:
 *   1. Register every explicit override (color+icon specified by the user).
 *   2. For agents missing a color, walk the palette from a hashed start index
 *      and pick the first slot whose hex isn't already taken — by a built-in,
 *      a prior override, or an earlier auto-assignment. Same for icons.
 *  This guarantees distinct visuals across all custom agents until you have
 *  more of them than there are palette slots. */
export function setCustomAgents(overrides: CustomAgentOverride[]): void {
  for (const key of Object.keys(_customRegistry)) delete _customRegistry[key];
  const usedHex = new Set<string>(Object.values(AGENTS).map((a) => a.hex.toLowerCase()));
  const usedIcons = new Set<LucideIcon>(Object.values(AGENTS).map((a) => a.icon));

  // Pass 1: explicit overrides land first so user choices always win.
  const deferred: CustomAgentOverride[] = [];
  for (const entry of overrides) {
    if (!entry?.name) continue;
    const explicitHex = entry.color?.match(/^#[0-9a-f]{3,8}$/i) ? entry.color : undefined;
    const explicitIconKey = entry.icon?.toLowerCase();
    const explicitIcon = explicitIconKey ? ICON_MAP[explicitIconKey] : undefined;
    if (!explicitHex || !explicitIcon) { deferred.push(entry); continue; }
    _customRegistry[entry.name] = {
      key: entry.name, label: entry.label || entry.name,
      hex: explicitHex, icon: explicitIcon, isCustom: true,
    };
    usedHex.add(explicitHex.toLowerCase());
    usedIcons.add(explicitIcon);
  }

  // Pass 2: auto-assign for the rest, skipping anything already used.
  for (const entry of deferred) {
    const start = hashIndex(entry.name, CUSTOM_DEFAULTS.length);
    let hex: string | undefined;
    let icon: LucideIcon | undefined;
    for (let i = 0; i < CUSTOM_DEFAULTS.length; i++) {
      const slot = CUSTOM_DEFAULTS[(start + i) % CUSTOM_DEFAULTS.length];
      if (!hex && !usedHex.has(slot.hex.toLowerCase())) hex = slot.hex;
      if (!icon && !usedIcons.has(slot.icon)) icon = slot.icon;
      if (hex && icon) break;
    }
    // Allow user-specified partial overrides to win.
    const explicitHex = entry.color?.match(/^#[0-9a-f]{3,8}$/i) ? entry.color : undefined;
    const explicitIconKey = entry.icon?.toLowerCase();
    const explicitIcon = explicitIconKey ? ICON_MAP[explicitIconKey] : undefined;
    const finalHex = explicitHex || hex || CUSTOM_DEFAULTS[start].hex;
    const finalIcon = explicitIcon || icon || CUSTOM_DEFAULTS[start].icon;
    _customRegistry[entry.name] = {
      key: entry.name, label: entry.label || entry.name,
      hex: finalHex, icon: finalIcon, isCustom: true,
    };
    usedHex.add(finalHex.toLowerCase());
    usedIcons.add(finalIcon);
  }
}

export function getAgent(key: string | undefined | null): AgentMeta {
  if (!key) return FALLBACK;
  const builtin = (AGENTS as Record<string, AgentMeta>)[key];
  if (builtin) return builtin;
  const custom = _customRegistry[key];
  if (custom) return custom;
  // Unknown name with no override yet — still distinct: hash to a default pair.
  const fallback = CUSTOM_DEFAULTS[hashIndex(key, CUSTOM_DEFAULTS.length)];
  return { key, label: key, hex: fallback.hex, icon: fallback.icon, isCustom: true };
}

export const ALL_AGENT_KEYS = Object.keys(AGENTS) as AgentKey[];
