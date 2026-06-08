import { headers } from "next/headers";

import { AdminBackLink } from "@/components/admin/admin-back-link";
import type { StageStats, Stats } from "./helpers";
import { emptyStats, formatTime, stageLabel } from "./helpers";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { cn } from "@/lib/utils";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

// ── Types ───────────────────────────────────────────────────────

type AiRun = {
  id: string;
  prompt_name: string;
  prompt_version: string;
  entity_type: string;
  entity_id: string;
  provider: string;
  model: string;
  status: "completed" | "failed";
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  latency_ms: number | null;
  error_message: string | null;
  trace_id: string | null;
  created_at: string;
};

type CostStats = {
  total_cost: number;
  avg_cost_per_run: number;
  cost_by_model: Record<string, number>;
  cost_by_stage: Record<string, number>;
  cost_by_month: Record<string, number>;
  top_entities: { entity: string; cost: number }[];
};

async function adminFetch(path: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user?.id) {
    return { ok: false, json: () => null as never };
  }
  const response = await fetch(`${backendBaseUrl}${path}`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });
  return response;
}

function formatCost(cents: number): string {
  if (cents < 0.01) return "$0.00";
  if (cents < 1) return `$${cents.toFixed(4)}`;
  if (cents < 100) return `$${cents.toFixed(2)}`;
  return `$${cents.toFixed(2)}`;
}

export default async function AiObservabilityPage() {
  const [statsRes, runsRes, costRes] = await Promise.all([
    adminFetch("/admin/ai-observability/stats"),
    adminFetch("/admin/ai-observability/runs?limit=30"),
    adminFetch("/admin/ai-observability/cost-stats"),
  ]);

  const stats: Stats = statsRes.ok ? await statsRes.json() : emptyStats();
  const runs: AiRun[] = runsRes.ok ? await runsRes.json() : [];
  const costStats: CostStats | null = costRes.ok ? await costRes.json() : null;

  const stageNames = Object.keys(stats.stages).sort();
  const maxLatency = Math.max(
    ...stageNames.map((s) => stats.stages[s].avg_latency_ms),
    1,
  );
  const maxTokens = Math.max(
    ...stageNames.map((s) => stats.stages[s].avg_total_tokens),
    1,
  );

  // Cost chart helpers
  const costModelEntries = costStats
    ? Object.entries(costStats.cost_by_model).sort(([, a], [, b]) => b - a)
    : [];
  const maxModelCost = costModelEntries.length > 0 ? costModelEntries[0][1] : 1;

  const costStageEntries = costStats
    ? Object.entries(costStats.cost_by_stage).sort(([, a], [, b]) => b - a)
    : [];
  const maxStageCost = costStageEntries.length > 0 ? costStageEntries[0][1] : 1;

  const costMonthEntries = costStats
    ? Object.entries(costStats.cost_by_month).sort(([a], [b]) => a.localeCompare(b))
    : [];
  const maxMonthCost = costMonthEntries.length > 0
    ? Math.max(...costMonthEntries.map(([, c]) => c))
    : 1;

  return (
    <div className={adminPageStackClass}>
      <AdminPageHeader
        title="AI Observability"
        description="AI run metrics, latency, token usage, and cost across all pipeline stages"
        actions={<AdminBackLink href="/admin">Back to dashboard</AdminBackLink>}
      />

      {/* ── Stat cards ── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total runs"
          value={stats.total_runs.toLocaleString()}
          color="text-foreground"
        />
        <StatCard
          label="Success rate"
          value={`${stats.success_rate}%`}
          color={
            stats.success_rate >= 90
              ? "text-emerald-600 dark:text-emerald-400"
              : stats.success_rate >= 70
                ? "text-amber-600 dark:text-amber-400"
                : "text-red-600 dark:text-red-400"
          }
        />
        <StatCard
          label="Avg latency"
          value={`${stats.avg_latency_ms.toFixed(0)}ms`}
          color="text-foreground"
        />
        <StatCard
          label="Total tokens"
          value={stats.total_tokens.toLocaleString()}
          color="text-foreground"
        />
      </div>

      {/* ── Stage breakdown ── */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Latency by stage */}
        <div className="rounded-xl border border-border/70 bg-card p-5">
          <h3 className="mb-4 text-sm font-semibold text-foreground">
            Avg latency by stage
          </h3>
          <div className="space-y-3">
            {stageNames.length === 0 ? (
              <NoDataMessage />
            ) : (
              stageNames.map((name) => {
                const s = stats.stages[name];
                const pct = (s.avg_latency_ms / maxLatency) * 100;
                return (
                  <div key={name}>
                    <div className="mb-1 flex items-center justify-between text-xs">
                      <span className="font-medium text-foreground">
                        {stageLabel(name)}
                      </span>
                      <span className="text-muted-foreground">
                        {s.avg_latency_ms.toFixed(0)}ms
                      </span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-brand transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Tokens by stage */}
        <div className="rounded-xl border border-border/70 bg-card p-5">
          <h3 className="mb-4 text-sm font-semibold text-foreground">
            Avg tokens by stage
          </h3>
          <div className="space-y-3">
            {stageNames.length === 0 ? (
              <NoDataMessage />
            ) : (
              stageNames.map((name) => {
                const s = stats.stages[name];
                const pct = (s.avg_total_tokens / maxTokens) * 100;
                return (
                  <div key={name}>
                    <div className="mb-1 flex items-center justify-between text-xs">
                      <span className="font-medium text-foreground">
                        {stageLabel(name)}
                      </span>
                      <span className="text-muted-foreground">
                        {s.avg_total_tokens.toFixed(0)} tok
                      </span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-sky-500 transition-all"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* ── Cost Dashboard ── */}
      {costStats && (
        <>
          {/* Cost stat cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Total AI cost"
              value={formatCost(costStats.total_cost)}
              color="text-amber-600 dark:text-amber-400"
            />
            <StatCard
              label="Avg cost per run"
              value={formatCost(costStats.avg_cost_per_run)}
              color="text-foreground"
            />
            <StatCard
              label="Models used"
              value={String(costModelEntries.length)}
              color="text-foreground"
            />
            <StatCard
              label="Stages billed"
              value={String(costStageEntries.length)}
              color="text-foreground"
            />
          </div>

          {/* Cost charts */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Cost by model */}
            <div className="rounded-xl border border-border/70 bg-card p-5">
              <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-foreground">
                <span className="size-2 rounded-full bg-amber-400" />
                Cost by model
              </h3>
              <div className="space-y-3">
                {costModelEntries.length === 0 ? (
                  <NoDataMessage />
                ) : (
                  costModelEntries.map(([model, cost]) => {
                    const pct = (cost / maxModelCost) * 100;
                    return (
                      <div key={model}>
                        <div className="mb-1 flex items-center justify-between text-xs">
                          <span className="font-medium text-foreground">{model}</span>
                          <span className="font-mono text-muted-foreground">
                            {formatCost(cost)}
                          </span>
                        </div>
                        <div className="h-2.5 overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full rounded-full bg-amber-400 transition-all"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Cost by stage */}
            <div className="rounded-xl border border-border/70 bg-card p-5">
              <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-foreground">
                <span className="size-2 rounded-full bg-violet-400" />
                Cost by stage
              </h3>
              <div className="space-y-3">
                {costStageEntries.length === 0 ? (
                  <NoDataMessage />
                ) : (
                  costStageEntries.map(([stage, cost]) => {
                    const pct = (cost / maxStageCost) * 100;
                    return (
                      <div key={stage}>
                        <div className="mb-1 flex items-center justify-between text-xs">
                          <span className="font-medium text-foreground">
                            {stageLabel(stage)}
                          </span>
                          <span className="font-mono text-muted-foreground">
                            {formatCost(cost)}
                          </span>
                        </div>
                        <div className="h-2.5 overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full rounded-full bg-violet-400 transition-all"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* Cost trend over time */}
          {costMonthEntries.length > 0 && (
            <div className="rounded-xl border border-border/70 bg-card p-5">
              <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-foreground">
                <span className="size-2 rounded-full bg-emerald-400" />
                Cost trend
              </h3>
              <div className="flex items-end gap-2 h-32">
                {costMonthEntries.map(([month, cost]) => {
                  const pct = (cost / maxMonthCost) * 100;
                  return (
                    <div
                      key={month}
                      className="group relative flex flex-1 flex-col items-center"
                    >
                      <div
                        className="w-full max-w-10 rounded-t-md bg-emerald-400/60 transition-all hover:bg-emerald-400"
                        style={{ height: `${Math.max(pct, 4)}%` }}
                        title={`${month}: ${formatCost(cost)}`}
                      />
                      <span className="mt-1 text-[9px] text-muted-foreground">
                        {month.slice(5)}
                      </span>
                      {/* Tooltip */}
                      <div className="absolute bottom-full mb-1 hidden rounded bg-foreground px-2 py-1 text-[10px] text-background shadow group-hover:block whitespace-nowrap">
                        {month}: {formatCost(cost)}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Top entities by cost */}
          {costStats.top_entities.length > 0 && (
            <div className="rounded-xl border border-border/70 bg-card">
              <div className="border-b border-border/50 px-5 py-4">
                <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground">
                  <span className="size-2 rounded-full bg-rose-400" />
                  Top entities by cost
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-border/30 text-xs text-muted-foreground">
                      <th className="px-5 py-3 font-medium">Entity</th>
                      <th className="px-5 py-3 font-medium text-right">Cost</th>
                      <th className="px-5 py-3 font-medium text-right">% of total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {costStats.top_entities.map((item) => {
                      const pct = (item.cost / costStats.total_cost) * 100;
                      return (
                        <tr
                          key={item.entity}
                          className="border-b border-border/20 transition-colors hover:bg-muted/30"
                        >
                          <td className="px-5 py-3 font-medium text-foreground">
                            {item.entity}
                          </td>
                          <td className="px-5 py-3 text-right font-mono text-muted-foreground">
                            {formatCost(item.cost)}
                          </td>
                          <td className="px-5 py-3 text-right text-muted-foreground">
                            {pct.toFixed(1)}%
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {/* ── Stage summary table ── */}
      <div className="rounded-xl border border-border/70 bg-card">
        <div className="border-b border-border/50 px-5 py-4">
          <h3 className="text-sm font-semibold text-foreground">
            Stage summary
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border/30 text-xs text-muted-foreground">
                <th className="px-5 py-3 font-medium">Stage</th>
                <th className="px-5 py-3 font-medium">Runs</th>
                <th className="px-5 py-3 font-medium">Avg latency</th>
                <th className="px-5 py-3 font-medium">Avg tokens</th>
                <th className="px-5 py-3 font-medium">Total tokens</th>
              </tr>
            </thead>
            <tbody>
              {stageNames.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-5 py-8 text-center text-muted-foreground">
                    No runs recorded yet
                  </td>
                </tr>
              ) : (
                stageNames.map((name) => {
                  const s = stats.stages[name];
                  return (
                    <tr
                      key={name}
                      className="border-b border-border/20 transition-colors hover:bg-muted/30"
                    >
                      <td className="px-5 py-3 font-medium text-foreground">
                        {stageLabel(name)}
                      </td>
                      <td className="px-5 py-3 text-muted-foreground">{s.count}</td>
                      <td className="px-5 py-3 text-muted-foreground">
                        {s.avg_latency_ms.toFixed(0)}ms
                      </td>
                      <td className="px-5 py-3 text-muted-foreground">
                        {s.avg_total_tokens.toFixed(0)}
                      </td>
                      <td className="px-5 py-3 text-muted-foreground">
                        {s.total_tokens.toLocaleString()}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Recent runs ── */}
      <div className="rounded-xl border border-border/70 bg-card">
        <div className="border-b border-border/50 px-5 py-4">
          <h3 className="text-sm font-semibold text-foreground">
            Recent runs
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border/30 text-xs text-muted-foreground">
                <th className="px-5 py-3 font-medium">Time</th>
                <th className="px-5 py-3 font-medium">Stage</th>
                <th className="px-5 py-3 font-medium">Entity</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Latency</th>
                <th className="px-5 py-3 font-medium">Tokens</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-8 text-center text-muted-foreground">
                    No runs recorded yet
                  </td>
                </tr>
              ) : (
                runs.map((run) => (
                  <tr
                    key={run.id}
                    className="border-b border-border/20 transition-colors hover:bg-muted/30"
                  >
                    <td className="whitespace-nowrap px-5 py-3 text-muted-foreground">
                      {formatTime(run.created_at)}
                    </td>
                    <td className="px-5 py-3">
                      <span className="font-medium text-foreground">
                        {stageLabel(run.prompt_name)}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      <span className="truncate max-w-[120px] inline-block align-bottom">
                        {run.entity_id}
                      </span>
                    </td>
                    <td className="px-5 py-3">
                      <StatusBadge status={run.status} />
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {run.latency_ms != null ? `${run.latency_ms}ms` : "—"}
                    </td>
                    <td className="px-5 py-3 text-muted-foreground">
                      {run.total_tokens != null
                        ? run.total_tokens.toLocaleString()
                        : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ── Sub-components ─────────────────────────────────────────────

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className="rounded-xl border border-border/70 bg-card p-5">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={cn("mt-1 text-2xl font-semibold tracking-tight", color)}>
        {value}
      </p>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
        status === "completed"
          ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-400"
          : "bg-red-50 text-red-700 dark:bg-red-950/30 dark:text-red-400",
      )}
    >
      <span
        className={cn(
          "inline-block size-1.5 rounded-full",
          status === "completed" ? "bg-emerald-500" : "bg-red-500",
        )}
      />
      {status}
    </span>
  );
}

function NoDataMessage() {
  return (
    <p className="py-4 text-center text-xs text-muted-foreground">
      No data yet
    </p>
  );
}
