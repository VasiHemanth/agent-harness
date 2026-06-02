import { AGENTS } from "@/data/agents";

export default function AgentsGrid() {
  return (
    <section id="agents" className="max-w-[1320px] mx-auto px-5 sm:px-8 py-16 sm:py-24">
      <div className="text-center mb-10 sm:mb-12">
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--tt-fg-dim)] mb-3">Supported</p>
        <h2 className="text-[28px] sm:text-[44px] leading-[1.1] tracking-[-0.02em] font-semibold text-[var(--tt-fg)] mb-4">
          Eleven agents. <span className="text-[var(--tt-brand)]">Zero config.</span>
        </h2>
        <p className="text-[14px] sm:text-[15px] text-[var(--tt-fg-muted)] max-w-2xl mx-auto leading-relaxed">
          TokenTelemetry reads logs your agents already write. No proxies, no wrappers, no SDK to register.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {AGENTS.map((a) => (
          <div
            key={a.name}
            className="group relative overflow-hidden rounded-[var(--tt-radius-lg)] border border-[var(--tt-border)] bg-[var(--tt-panel)] p-5 transition-colors hover:border-[var(--tt-border-strong)]"
          >
            <span
              aria-hidden
              className="pointer-events-none absolute inset-x-0 -top-px h-px"
              style={{ background: `linear-gradient(90deg, transparent, ${a.hex}55, transparent)` }}
            />
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="min-w-0">
                <div className="text-[15px] font-semibold tracking-[-0.01em] text-[var(--tt-fg)] truncate">
                  {a.name}
                </div>
                <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-[var(--tt-fg-dim)] mt-0.5">
                  {a.vendor}
                </div>
              </div>
              <span
                className="h-7 w-7 grid place-items-center rounded-md border shrink-0"
                style={{ backgroundColor: `${a.hex}14`, borderColor: `${a.hex}33`, color: a.hex }}
              >
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: a.hex, boxShadow: `0 0 8px ${a.hex}80` }} />
              </span>
            </div>

            <div className="flex flex-wrap gap-1.5 mb-3">
              {a.captures.map((c) => (
                <span
                  key={c}
                  className="text-[10px] font-medium text-[var(--tt-fg-muted)] tt-tint-1 border border-[var(--tt-border)] px-1.5 py-0.5 rounded uppercase tracking-tight"
                >
                  {c}
                </span>
              ))}
            </div>

            <div className="text-[10.5px] font-mono text-[var(--tt-fg-dim)] truncate" title={a.logPath}>
              <span className="text-[var(--tt-fg-faint)]">reads:</span> {a.logPath}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
