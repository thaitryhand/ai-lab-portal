// Pure helper functions extracted from page.tsx for testability.

export function emptyStats() {
  return {
    total_runs: 0,
    completed: 0,
    failed: 0,
    success_rate: 0,
    avg_latency_ms: 0,
    avg_total_tokens: 0,
    total_tokens: 0,
    stages: {} as Record<string, { count: number; avg_latency_ms: number; avg_total_tokens: number; total_tokens: number }>,
  };
}

export function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const STAGE_LABELS: Record<string, string> = {
  blog_idea: "Idea",
  blog_outline: "Outline",
  draft_writer: "Draft",
  draft_section_writer: "Draft (section)",
  technical_review: "Review",
  marketing_metadata: "Marketing",
  claim_extraction: "Claims",
  ai_news_scoring: "News scoring",
};

export function stageLabel(name: string): string {
  return STAGE_LABELS[name] ?? name;
}

export type StageStats = {
  count: number;
  avg_latency_ms: number;
  avg_total_tokens: number;
  total_tokens: number;
};

export type Stats = ReturnType<typeof emptyStats>;
