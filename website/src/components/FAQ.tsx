export const FAQ_ITEMS = [
  {
    q: "How do I track Claude Code token usage?",
    a: "Install TokenTelemetry, run Claude Code normally, and open http://localhost:3000. TokenTelemetry auto-detects Claude Code sessions from ~/.claude/ logs — no instrumentation, no SDK, no config.",
  },
  {
    q: "How do I monitor Gemini CLI and Codex costs?",
    a: "TokenTelemetry auto-reads logs from Gemini CLI, OpenAI Codex CLI, Cursor, Copilot, Qwen, OpenCode, Vibe, and Antigravity. Token counts and dollar costs appear in the local dashboard automatically.",
  },
  {
    q: "Is there a free tool to monitor AI coding agent token usage?",
    a: "Yes — TokenTelemetry is free, open-source (MIT), and runs 100% locally. No account, no signup, no cloud.",
  },
  {
    q: "Does TokenTelemetry send my data to the cloud?",
    a: "No. Everything runs on your machine. The dashboard reads session log files from your local filesystem and serves a UI on localhost. Nothing leaves your computer.",
  },
  {
    q: "How does TokenTelemetry compare to Langfuse or Helicone?",
    a: "TokenTelemetry is purpose-built for AI coding agents and is zero-config — no SDK instrumentation. Langfuse and Helicone are general LLM-app observability platforms that require code changes and (typically) a cloud account.",
  },
  {
    q: "Which coding agents does it support?",
    a: "Claude Code (Anthropic), OpenAI Codex CLI, Gemini CLI (Google), Cursor, GitHub Copilot, Qwen, OpenCode, Vibe, and Antigravity — 9 agents total.",
  },
];

export default function FAQ() {
  return (
    <section className="border-t border-slate-800/50 bg-slate-950">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-20 sm:py-28">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-[10px] font-bold text-blue-400 uppercase tracking-widest mb-4">
            FAQ
          </div>
          <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tighter">
            Common questions
          </h2>
        </div>
        <div className="space-y-3">
          {FAQ_ITEMS.map((item, i) => (
            <details
              key={i}
              className="group rounded-xl border border-slate-800/80 bg-slate-900/40 px-5 py-4 open:bg-slate-900/70 transition-colors"
            >
              <summary className="flex items-center justify-between cursor-pointer list-none gap-4">
                <h3 className="text-white font-semibold text-base sm:text-lg">{item.q}</h3>
                <span className="text-slate-500 text-2xl leading-none transition-transform group-open:rotate-45 select-none">
                  +
                </span>
              </summary>
              <p className="mt-3 text-slate-400 leading-relaxed text-sm sm:text-base">
                {item.a}
              </p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
