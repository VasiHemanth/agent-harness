"use client";

import { api } from "./api";

// ---- Backend API contract types (see backend on :8010) ----

export interface SummarizerBackend {
  name: string;
  display_name: string;
}

export interface SummarizerConfig {
  enabled: boolean;
  backend: string | null;
  model: string | null;
}

export interface SummaryBrief {
  intent: string;
  final_text: string;
  user_turns: number;
  tools: Record<string, number>;
  files: string[];
  commands: string[];
  errors: string[];
  tokens: { input: number; output: number; total: number };
  cost: number;
  model: string | null;
  agent: string;
  project: string;
}

export interface SummaryNarrative {
  intent_outcome?: string;
  actions?: string[];
  efficiency?: string;
  notable?: string[];
}

export interface Summary {
  session_id: string;
  agent: string;
  content_hash: string;
  backend: string;
  model: string | null;
  brief: SummaryBrief;
  narrative: SummaryNarrative | null;
  summary_cost: number;
  generated_at: string;
  stale: boolean;
}

export interface RecentTally {
  requested: number;
  summarized: number;
  skipped: number;
  failed: number;
}

// ---- API helpers (all go through api<T>/API_BASE, never hardcoded URLs) ----

export const getSummarizerConfig = () => api<SummarizerConfig>("/config/summarizer");

export const getAvailableBackends = () =>
  api<{ backends: SummarizerBackend[] }>("/summarizer/available").then((r) => r.backends);

export interface OllamaModel {
  name: string;
  size: string;
  modified: string;
}
export const listOllamaModels = () =>
  api<{ models: OllamaModel[] }>("/summarizer/ollama/models").then((r) => r.models);

export const putSummarizerConfig = (cfg: SummarizerConfig) =>
  api<SummarizerConfig>("/config/summarizer", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cfg),
  });

export const getCachedSummary = (sessionId: string) =>
  api<{ summary: Summary | null }>(`/sessions/${sessionId}/summary`).then((r) => r.summary);

export const generateSummary = (sessionId: string, agent: string, force = false) =>
  api<{ summary: Summary; error: string | null }>(
    `/sessions/${sessionId}/summary?agent=${encodeURIComponent(agent)}&force=${force}`,
    { method: "POST" },
  );

export const summarizeRecent = (limit: number) =>
  api<RecentTally>(`/summaries/recent?limit=${limit}`, { method: "POST" });

/**
 * Config is "unset" (never configured by the user) when AI summaries are off
 * AND no backend has been chosen — that's the signal to show first-run onboarding.
 */
export const isConfigUnset = (cfg: SummarizerConfig) => !cfg.enabled && cfg.backend == null;

export const ONBOARDING_FLAG = "tt-summarizer-onboarded";
