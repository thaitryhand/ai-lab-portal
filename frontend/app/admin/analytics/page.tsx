import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { Activity, ExternalLink, Eye, Globe, MessageSquare, MousePointer2, Share2, TrendingUp, Users } from "lucide-react";

import { AdminDashboardHeader } from "@/components/admin/admin-dashboard-header";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { auth } from "@/lib/auth/server";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type Summary = {
  total_views_today: number;
  total_views_7d: number;
  total_views_30d: number;
  total_views_all: number;
  unique_visitors_30d: number;
  total_events_30d: number;
  shares_30d: number;
  clicks_30d: number;
  comments_30d: number;
};

type TopContentItem = { path: string; views: number };
type TrendPoint = { date: string; views: number };
type ReferrerItem = { referrer: string; views: number };

async function fetchJson<T>(url: string): Promise<T | null> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return null;
  try {
    const res = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...createAdminBoundaryHeaders({
          user: { id: session.user.id, email: session.user.email },
        }),
      },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

function SummaryCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | number }) {
  return (
    <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        {icon}
        {label}
      </div>
      <p className="mt-1 text-2xl font-bold tabular-nums">
        {typeof value === "number" ? value.toLocaleString() : value}
      </p>
    </div>
  );
}

function TrendBar({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="flex items-center gap-2">
      <div className="h-8 w-full rounded-md bg-muted/50">
        <div
          className="h-full rounded-md bg-brand/60 transition-all duration-300"
          style={{ width: `${Math.max(pct, 2)}%` }}
        />
      </div>
      <span className="w-12 text-right text-xs tabular-nums text-muted-foreground">{value}</span>
    </div>
  );
}

export default async function AnalyticsPage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const base = `${backendBaseUrl}/admin/analytics`;
  const [summary, topContent, trends, referrers] = await Promise.all([
    fetchJson<Summary>(`${base}/summary`),
    fetchJson<TopContentItem[]>(`${base}/top-content?days=30&limit=10`),
    fetchJson<TrendPoint[]>(`${base}/trends?days=30`),
    fetchJson<ReferrerItem[]>(`${base}/referrers?days=30&limit=10`),
  ]);

  return (
    <div className={adminPageStackClass}>
      <AdminDashboardHeader
        title="Analytics"
        description="Page view metrics across all public pages."
        email={session.user.email}
      />

      {/* Summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <SummaryCard icon={<Eye className="h-4 w-4" />} label="All time" value={summary?.total_views_all ?? "—"} />
        <SummaryCard icon={<Activity className="h-4 w-4" />} label="Last 30 days" value={summary?.total_views_30d ?? "—"} />
        <SummaryCard icon={<TrendingUp className="h-4 w-4" />} label="Last 7 days" value={summary?.total_views_7d ?? "—"} />
        <SummaryCard icon={<Eye className="h-4 w-4" />} label="Today" value={summary?.total_views_today ?? "—"} />
        <SummaryCard icon={<Users className="h-4 w-4" />} label="Unique visitors (30d)" value={summary?.unique_visitors_30d ?? "—"} />
      </div>

      {/* Event summary cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard icon={<Share2 className="h-4 w-4" />} label="Shares (30d)" value={summary?.shares_30d ?? "—"} />
        <SummaryCard icon={<MousePointer2 className="h-4 w-4" />} label="Clicks (30d)" value={summary?.clicks_30d ?? "—"} />
        <SummaryCard icon={<MessageSquare className="h-4 w-4" />} label="Comments (30d)" value={summary?.comments_30d ?? "—"} />
        <SummaryCard icon={<Activity className="h-4 w-4" />} label="All events (30d)" value={summary?.total_events_30d ?? "—"} />
      </div>

      {/* Views over time (CSS bar chart) */}
      <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
        <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold">
          <Activity className="h-4 w-4" />
          Views over time (last 30 days)
        </h3>
        {trends && trends.length > 0 ? (
          <div className="space-y-1">
            {trends.map((point) => (
              <TrendBar key={point.date} value={point.views} max={Math.max(...trends.map((t) => t.views), 1)} />
            ))}
          </div>
        ) : (
          <p className="py-8 text-center text-sm text-muted-foreground">No page view data yet.</p>
        )}
      </div>

      {/* Top content */}
      <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
        <div className="border-b px-6 py-4">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <TrendingUp className="h-4 w-4" />
            Top content (last 30 days)
          </h3>
        </div>
        {topContent && topContent.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs font-medium text-muted-foreground">
                  <th className="px-6 py-3 w-12">#</th>
                  <th className="px-4 py-3">Page</th>
                  <th className="px-4 py-3 text-right">Views</th>
                </tr>
              </thead>
              <tbody>
                {topContent.map((item, i) => (
                  <tr key={item.path} className="border-b last:border-0 hover:bg-muted/30">
                    <td className="px-6 py-3 text-xs text-muted-foreground">{i + 1}</td>
                    <td className="px-4 py-3">
                      <a
                        href={item.path}
                        className="inline-flex items-center gap-1 font-medium hover:text-brand hover:underline"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {item.path}
                        <ExternalLink className="h-3 w-3 shrink-0 opacity-50" />
                      </a>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">{item.views.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center px-6 py-12 text-center text-sm text-muted-foreground">
            <Eye className="mb-2 h-8 w-8 opacity-40" />
            <p>No page view data yet</p>
            <p className="text-xs">Views will appear after visitors browse the public pages.</p>
          </div>
        )}
      </div>

      {/* Referrers */}
      <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
        <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold">
          <Globe className="h-4 w-4" />
          Referrers (last 30 days)
        </h3>
        {referrers && referrers.length > 0 ? (
          <div className="space-y-2">
            {referrers.map((ref) => {
              const maxViews = Math.max(...referrers.map((r) => r.views), 1);
              const pct = (ref.views / maxViews) * 100;
              return (
                <div key={ref.referrer} className="flex items-center gap-3">
                  <span className="w-48 truncate text-sm font-medium">{ref.referrer}</span>
                  <div className="h-5 flex-1 rounded bg-muted/50">
                    <div
                      className="h-full rounded bg-brand/50"
                      style={{ width: `${Math.max(pct, 2)}%` }}
                    />
                  </div>
                  <span className="w-16 text-right text-xs tabular-nums text-muted-foreground">
                    {ref.views.toLocaleString()}
                  </span>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="py-4 text-center text-sm text-muted-foreground">No referrer data yet.</p>
        )}
      </div>
    </div>
  );
}
