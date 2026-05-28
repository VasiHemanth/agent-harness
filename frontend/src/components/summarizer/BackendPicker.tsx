"use client";

import { useEffect, useState } from "react";
import { Check, Ban } from "lucide-react";
import { getAgent } from "@/lib/agents";
import { cn } from "@/lib/cn";
import {
  listOllamaModels,
  type OllamaModel,
  type SummarizerBackend,
} from "@/lib/summarizer";

interface BackendPickerProps {
  backends: SummarizerBackend[];
  /** null == "Skip / no AI summaries" selected */
  selected: string | null;
  onSelect: (backend: string | null) => void;
  /** Whether to render the "no AI summaries" opt-out tile. */
  allowSkip?: boolean;
  /** Currently chosen Ollama model (only meaningful when selected === "ollama"). */
  model?: string | null;
  /** Notified when the user picks a different Ollama model. */
  onModelChange?: (model: string | null) => void;
}

/**
 * Shared backend selector — reused by the first-run onboarding modal and the
 * settings surface. Tints each option by its agent hex via getAgent().
 *
 * When Ollama is the active tile, a sub-dropdown appears so the user can pin
 * a specific installed model (Ollama can otherwise be very slow on a heavy
 * default). Model list is fetched lazily on first Ollama selection.
 */
export function BackendPicker({
  backends, selected, onSelect, allowSkip = true,
  model = null, onModelChange,
}: BackendPickerProps) {
  const [models, setModels] = useState<OllamaModel[] | null>(null);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsErr, setModelsErr] = useState<string | null>(null);

  // Lazy-load Ollama models the first time the Ollama tile is selected, so
  // users who never pick it don't pay the `ollama list` shell-out.
  useEffect(() => {
    if (selected !== "ollama" || models !== null || modelsLoading) return;
    setModelsLoading(true);
    listOllamaModels()
      .then((list) => setModels(list))
      .catch((e) => setModelsErr(e instanceof Error ? e.message : String(e)))
      .finally(() => setModelsLoading(false));
  }, [selected, models, modelsLoading]);

  return (
    <div className="space-y-3">
      <div className="grid gap-2">
        {backends.map((b) => {
          const meta = getAgent(b.name);
          const Icon = meta.icon;
          const active = selected === b.name;
          const isOllama = b.name === "ollama";
          return (
            <div key={b.name}>
              <button
                type="button"
                onClick={() => onSelect(b.name)}
                className={cn(
                  "group relative w-full flex items-center gap-3 rounded-[var(--tt-radius-lg)] border px-3.5 py-3 text-left transition-colors",
                  active
                    ? "border-[var(--tt-border-strong)] bg-[var(--tt-raised)]"
                    : "border-[var(--tt-border)] bg-[var(--tt-panel)] hover:border-[var(--tt-border-strong)] hover:bg-[var(--tt-sunken)]",
                )}
              >
                <div
                  className="h-8 w-8 shrink-0 grid place-items-center rounded-md"
                  style={{ backgroundColor: `${meta.hex}14`, color: meta.hex }}
                >
                  <Icon size={16} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-[13px] font-semibold text-[var(--tt-fg)] truncate">{b.display_name}</div>
                  <div className="text-[11px] text-[var(--tt-fg-dim)] truncate">
                    Summaries generated locally via {b.display_name}.
                  </div>
                </div>
                {active && (
                  <span
                    className="h-5 w-5 grid place-items-center rounded-full"
                    style={{ backgroundColor: meta.hex, color: "#fff" }}
                  >
                    <Check size={12} strokeWidth={3} />
                  </span>
                )}
              </button>

              {/* Ollama-specific model picker — appears below the tile when active. */}
              {active && isOllama && (
                <div className="mt-2 ml-11 mr-1">
                  <label className="block text-[10.5px] font-medium uppercase tracking-[0.1em] text-[var(--tt-fg-muted)] mb-1.5">
                    Model
                  </label>
                  {modelsLoading ? (
                    <div className="text-[12px] text-[var(--tt-fg-dim)] italic">Loading installed models…</div>
                  ) : modelsErr ? (
                    <div className="text-[12px] text-[var(--tt-danger-fg)]">{modelsErr}</div>
                  ) : models && models.length === 0 ? (
                    <div className="text-[12px] text-[var(--tt-fg-dim)]">
                      No Ollama models installed. Run <code className="font-mono">ollama pull llama3</code> (or similar) first.
                    </div>
                  ) : models ? (
                    <select
                      value={model ?? ""}
                      onChange={(e) => onModelChange?.(e.target.value || null)}
                      className="w-full h-9 px-3 rounded-md bg-[var(--tt-sunken)] border border-[var(--tt-border-strong)] text-[13px] text-[var(--tt-fg)] focus:outline-none focus:border-[var(--tt-border-focus)] transition-colors"
                    >
                      <option value="">Auto — use first installed</option>
                      {models.map((m) => (
                        <option key={m.name} value={m.name}>
                          {m.name}{m.size ? ` · ${m.size}` : ""}
                        </option>
                      ))}
                    </select>
                  ) : null}
                  {model && (
                    <p className="text-[10.5px] text-[var(--tt-fg-dim)] mt-1.5">
                      Local inference is CPU-bound — larger models will take several minutes per summary.
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}

        {allowSkip && (
          <button
            type="button"
            onClick={() => onSelect(null)}
            className={cn(
              "flex items-center gap-3 rounded-[var(--tt-radius-lg)] border px-3.5 py-3 text-left transition-colors",
              selected === null
                ? "border-[var(--tt-border-strong)] bg-[var(--tt-raised)]"
                : "border-[var(--tt-border)] bg-[var(--tt-panel)] hover:border-[var(--tt-border-strong)] hover:bg-[var(--tt-sunken)]",
            )}
          >
            <div className="h-8 w-8 shrink-0 grid place-items-center rounded-md tt-tint-2 text-[var(--tt-fg-dim)]">
              <Ban size={16} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-[13px] font-semibold text-[var(--tt-fg)]">Skip — no AI summaries</div>
              <div className="text-[11px] text-[var(--tt-fg-dim)]">
                Only the deterministic brief is shown. Nothing leaves your machine.
              </div>
            </div>
            {selected === null && (
              <span className="h-5 w-5 grid place-items-center rounded-full bg-[var(--tt-fg-muted)] text-[var(--tt-canvas)]">
                <Check size={12} strokeWidth={3} />
              </span>
            )}
          </button>
        )}
      </div>
    </div>
  );
}
