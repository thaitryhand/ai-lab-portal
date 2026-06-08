import { headers } from "next/headers";
import { redirect } from "next/navigation";
import {
  AlertCircle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  GitBranch,
  Inbox,
} from "lucide-react";

import { AdminBackLink } from "@/components/admin/admin-back-link";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { cn } from "@/lib/utils";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

/* ── Types ── */

type StageDistItem = {
  stage: string;
  label: string;
  count: number;
  color: string;
};

type CycleTime = {
  avg_days: number;
  min_days: number;
  max_days: number;
};

type Overview = {
  total_ideas: number;
  in_pipeline: number;
  published_count: number;
  rejected_count: number;
  stage_distribution: StageDistItem[];
  stage_queues: Record<string, { id: string; title: string; stage: string; created_at: string | null }[]>;
  monthly_throughput: Record<string, number>;
  monthly_created: Record<string, number>;
  cycle_time: CycleTime;
};

type IdeaItem = {
  id: string;
  title: string;
  stage: string;
  stage_label: string;
  stage_order: number;
  status: string;
  created_at: string | null;
  scheduled_at: string | null;
  outline_status: string | null;
  draft_status: string | null;
  review_status: string | null;
  marketing_status: string | null;
  seo_status: string | null;
  published_post_id: string | null;
};

/* ── Data fetching ── */

async function fetchOverview(): Promise<Overview | null> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return null;
  try {
    const res = await fetch(`${backendBaseUrl}/admin/pipeline-dashboard/overview`, {
      headers: createAdminBoundaryHeaders({ user: { id: session.user.id, email: session.user.email } }),
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

async function fetchIdeas(): Promise<IdeaItem[]> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return [];
  try {
    const res = await fetch(`${backendBaseUrl}/admin/pipeline-dashboard/ideas`, {
      headers: createAdminBoundaryHeaders({ user: { id: session.user.id, email: session.user.email } }),
      cache: "no-store",
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

/* ── Sub-components ── */

function StatCard({
  icon: Icon,
  label,
  value,
  hint,
  color = "text-foreground",
}: {
  icon: typeof BarChart3;
  label: string;
  value: string | number;
  hint?: string;
  color?: string;
}) {
  return (
    <div className="rounded-xl border border-border/60 bg-card p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-1">{label}</p>
          <p className={cn("text-2xl font-bold", color)}>{value}</p>
          {hint && <p className="text-xs text-muted-foreground mt-1">{hint}</p>}
        </div>
        <span className="rounded-lg border border-border/40 bg-muted/30 p-2 text-muted-foreground">
          <Icon className="size-4" />
        </span>
      </div>
    </div>
  );
}

function StageBarChart({ stages }: { stages: StageDistItem[] }) {
  if (stages.length === 0) return null;
  const maxCount = Math.max(...stages.map((s) => s.count), 1);

  return (
    <div className="rounded-xl border border-border/60 bg-card p-4">
      <h3 className="text-sm font-semibold mb-4">Stage Distribution</h3>
      <div className="space-y-2">
        {stages.map((s) => {
          const pct = (s.count / maxCount) * 100;
          return (
            <div key={s.stage} className="flex items-center gap-3">
              <span className="w-20 text-xs font-medium text-muted-foreground shrink-0">
                {s.label}
              </span>
              <div className="flex-1 h-6 rounded-full bg-muted/50 overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.max(pct, s.count > 0 ? 4 : 0)}%`,
                    backgroundColor: s.color,
                  }}
                />
              </div>
              <span className="w-8 text-right text-xs font-semibold text-foreground">
                {s.count}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ThroughputChart({
  throughput,
  created,
}: {
  throughput: Record<string, number>;
  created: Record<string, number>;
}) {
  const allMonths = new Set([...Object.keys(throughput), ...Object.keys(created)]);
  const sortedMonths = [...allMonths].sort();
  const recent = sortedMonths.slice(-12);
  const maxVal = Math.max(
    ...recent.map((m) => Math.max(throughput[m] ?? 0, created[m] ?? 0)),
    1,
  );

  return (
    <div className="rounded-xl border border-border/60 bg-card p-4">
      <h3 className="text-sm font-semibold mb-4">Monthly Throughput</h3>
      <div className="flex items-end gap-2 h-36">
        {recent.map((month) => {
          const t = throughput[month] ?? 0;
          const c = created[month] ?? 0;
          const [y, m] = month.split("-");
          const label = new Date(Number(y), Number(m) - 1).toLocaleDateString("en-US", {
            month: "short",
          });
          return (
            <div key={month} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
              <span className="text-[9px] text-muted-foreground">{t + c}</span>
              <div className="w-full flex flex-col-reverse gap-px" style={{ height: `${Math.max(((t + c) / maxVal) * 100, 2)}%` }}>
                <div
                  className="w-full rounded-t transition-all"
                  style={{ height: `${(t / Math.max(t + c, 1)) * 100}%`, backgroundColor: "#22c55e" }}
                  title={`Published: ${t}`}
                />
                <div
                  className="w-full transition-all"
                  style={{ height: `${(c / Math.max(t + c, 1)) * 100}%`, backgroundColor: "#3b82f6" }}
                  title={`Created: ${c}`}
                />
              </div>
              <span className="text-[9px] text-muted-foreground">{label}</span>
            </div>
          );
        })}
      </div>
      <div className="flex items-center gap-4 mt-3 text-[11px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="size-2 rounded-sm" style={{ backgroundColor: "#22c55e" }} /> Published
        </span>
        <span className="flex items-center gap-1">
          <span className="size-2 rounded-sm" style={{ backgroundColor: "#3b82f6" }} /> Created
        </span>
      </div>
    </div>
  );
}

function GanttView({ ideas }: { ideas: IdeaItem[] }) {
  if (ideas.length === 0) {
    return (
      <div className="rounded-xl border border-border/60 bg-card p-8 text-center text-sm text-muted-foreground">
        No pipeline ideas yet. Create blog ideas to see them here.
      </div>
    );
  }

  const activeIdeas = ideas.filter((i) => i.status !== "rejected").slice(0, 20);

  return (
    <div className="rounded-xl border border-border/60 bg-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border/60 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <th className="px-4 py-3 min-w-[200px]">Idea</th>
              <th className="px-4 py-3 text-center">Idea</th>
              <th className="px-4 py-3 text-center">Approved</th>
              <th className="px-4 py-3 text-center">Outline</th>
              <th className="px-4 py-3 text-center">Draft</th>
              <th className="px-4 py-3 text-center">Reviewed</th>
              <th className="px-4 py-3 text-center">Marketing</th>
              <th className="px-4 py-3 text-center">SEO</th>
              <th className="px-4 py-3 text-center">Published</th>
            </tr>
          </thead>
          <tbody>
            {activeIdeas.map((idea, i) => {
              const stageOrder = ["idea", "approved", "outline_done", "draft_done", "reviewed", "marketing_done", "seo_done", "published"];
              const currentIdx = stageOrder.indexOf(idea.stage);
              return (
                <tr
                  key={idea.id}
                  className={cn(
                    "border-b border-border/30 transition-colors hover:bg-muted/30",
                    i === activeIdeas.length - 1 && "border-b-0",
                    idea.published_post_id && "bg-emerald-50/30 dark:bg-emerald-950/10",
                  )}
                >
                  <td className="px-4 py-3">
                    <a
                      href={`/admin/blog-ideas/${idea.id}`}
                      className="font-medium text-foreground hover:text-brand transition-colors text-xs"
                    >
                      {idea.title}
                    </a>
                    {idea.created_at && (
                      <p className="text-[10px] text-muted-foreground mt-0.5">
                        {new Date(idea.created_at).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        })}
                      </p>
                    )}
                  </td>
                  {stageOrder.map((stage, si) => {
                    const isActive = si <= currentIdx;
                    const isCurrent = si === currentIdx;
                    return (
                      <td key={stage} className="px-2 py-3 text-center">
                        <span
                          className={cn(
                            "inline-flex items-center justify-center size-6 rounded-full transition-all",
                            isCurrent
                              ? "ring-2 ring-offset-1"
                              : "",
                          )}
                          style={{
                            backgroundColor: isActive ? (stage === "published" ? "#22c55e" : "#e2e8f0") : "transparent",
                            borderColor: stage === "published" ? "#22c55e" : "#e2e8f0",
                            borderWidth: isActive ? 0 : 1,
                          }}
                        >
                          {isActive && (
                            <span className="text-[10px] font-bold" style={{ color: stage === "published" ? "#fff" : "#64748b" }}>
                              {isCurrent ? "●" : "✓"}
                            </span>
                          )}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function StatsPanel({ cycleTime }: { cycleTime: CycleTime }) {
  return (
    <div className="rounded-xl border border-border/60 bg-card p-4">
      <h3 className="text-sm font-semibold mb-4">Cycle Time</h3>
      <div className="space-y-4">
        <div>
          <p className="text-xs text-muted-foreground mb-1">Average (days)</p>
          <p className="text-3xl font-bold text-foreground">{cycleTime.avg_days}</p>
        </div>
        <div className="flex gap-4">
          <div className="flex-1">
            <p className="text-[10px] text-muted-foreground mb-0.5">Min</p>
            <p className="text-lg font-semibold text-emerald-600">{cycleTime.min_days}</p>
          </div>
          <div className="flex-1">
            <p className="text-[10px] text-muted-foreground mb-0.5">Max</p>
            <p className="text-lg font-semibold text-amber-600">{cycleTime.max_days}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function PipelineFlow({ stages }: { stages: StageDistItem[] }) {
  if (stages.length === 0) return null;
  const activeStages = stages.filter((s) => s.stage !== "published");

  return (
    <div className="rounded-xl border border-border/60 bg-card p-4">
      <h3 className="text-sm font-semibold mb-4">Pipeline Flow</h3>
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2">
        {activeStages.map((s, i) => (
          <div key={s.stage} className="flex items-center gap-1.5 shrink-0">
            <div
              className="flex flex-col items-center gap-1 rounded-lg px-3 py-2 min-w-[72px]"
              style={{ backgroundColor: `${s.color}15` }}
            >
              <span className="text-xs font-semibold text-foreground">{s.count}</span>
              <span className="text-[9px] text-muted-foreground whitespace-nowrap">{s.label}</span>
            </div>
            {i < activeStages.length - 1 && (
              <ArrowRight className="size-3 text-muted-foreground/40 shrink-0" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Page ── */

export default async function PipelineDashboardPage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const [overview, ideas] = await Promise.all([fetchOverview(), fetchIdeas()]);

  return (
    <div className={adminPageStackClass}>
      <AdminPageHeader
        title="Pipeline Dashboard"
        description="AI content pipeline — from idea to published"
        actions={<AdminBackLink href="/admin">Back to dashboard</AdminBackLink>}
      />

      {/* Stats */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Inbox} label="Total Ideas" value={overview?.total_ideas ?? 0} />
        <StatCard icon={GitBranch} label="In Pipeline" value={overview?.in_pipeline ?? 0} color="text-amber-600 dark:text-amber-400" />
        <StatCard icon={CheckCircle2} label="Published" value={overview?.published_count ?? 0} color="text-emerald-600 dark:text-emerald-400" />
        <StatCard icon={AlertCircle} label="Rejected" value={overview?.rejected_count ?? 0} color="text-red-600 dark:text-red-400" />
      </div>

      {/* Pipeline flow + Cycle time */}
      {overview && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <PipelineFlow stages={overview.stage_distribution} />
          </div>
          <StatsPanel cycleTime={overview.cycle_time} />
        </div>
      )}

      {/* Stage distribution + Throughput */}
      {overview && (
        <div className="grid gap-6 lg:grid-cols-2">
          <StageBarChart stages={overview.stage_distribution} />
          <ThroughputChart throughput={overview.monthly_throughput} created={overview.monthly_created} />
        </div>
      )}

      {/* Gantt-like view */}
      <div>
        <h2 className="text-sm font-semibold mb-3">Pipeline Overview (Gantt)</h2>
        <GanttView ideas={ideas} />
      </div>
    </div>
  );
}
