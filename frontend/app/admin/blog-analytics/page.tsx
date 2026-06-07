import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { Activity, BarChart3, Eye, TrendingUp, Users } from "lucide-react";

import { AdminDashboardHeader } from "@/components/admin/admin-dashboard-header";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { auth } from "@/lib/auth/server";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type AnalyticsSummary = {
  total_views: number;
  total_unique_visitors: number;
  views_today: number;
  views_this_week: number;
  views_this_month: number;
  top_posts: {
    post_id: string;
    title: string;
    total_views: number;
    unique_visitors: number;
    views_today: number;
    views_this_week: number;
  }[];
};

async function fetchAnalytics(): Promise<AnalyticsSummary | null> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return null;

  try {
    const res = await fetch(`${backendBaseUrl}/admin/blog-analytics/summary`, {
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

export default async function BlogAnalyticsPage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const analytics = await fetchAnalytics();

  return (
    <div className={adminPageStackClass}>
      <AdminDashboardHeader
        icon={BarChart3}
        title="Blog Analytics"
        description="Content performance metrics and reader engagement."
      />

      {/* Stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Eye className="h-4 w-4" />
            Total views
          </div>
          <p className="mt-1 text-2xl font-bold tabular-nums">
            {analytics?.total_views?.toLocaleString() ?? "—"}
          </p>
        </div>
        <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Users className="h-4 w-4" />
            Unique visitors
          </div>
          <p className="mt-1 text-2xl font-bold tabular-nums">
            {analytics?.total_unique_visitors?.toLocaleString() ?? "—"}
          </p>
        </div>
        <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Activity className="h-4 w-4" />
            Views today
          </div>
          <p className="mt-1 text-2xl font-bold tabular-nums">
            {analytics?.views_today?.toLocaleString() ?? "—"}
          </p>
        </div>
        <div className="rounded-lg border bg-card p-4 text-card-foreground shadow-sm">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <TrendingUp className="h-4 w-4" />
            This week
          </div>
          <p className="mt-1 text-2xl font-bold tabular-nums">
            {analytics?.views_this_week?.toLocaleString() ?? "—"}
          </p>
        </div>
      </div>

      {/* Period breakdown */}
      <div className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
        <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold">
          <BarChart3 className="h-4 w-4" />
          Period breakdown
        </h3>
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            { label: "Today", value: analytics?.views_today },
            { label: "This week", value: analytics?.views_this_week },
            { label: "This month", value: analytics?.views_this_month },
          ].map((period) => (
            <div key={period.label} className="rounded-md border bg-muted/30 p-3">
              <p className="text-xs text-muted-foreground">{period.label}</p>
              <p className="mt-1 text-xl font-bold tabular-nums">
                {period.value?.toLocaleString() ?? "—"}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Top posts table */}
      <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
        <div className="border-b px-6 py-4">
          <h3 className="flex items-center gap-2 text-sm font-semibold">
            <TrendingUp className="h-4 w-4" />
            Top content
          </h3>
        </div>
        {analytics?.top_posts && analytics.top_posts.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs font-medium text-muted-foreground">
                  <th className="px-6 py-3">Post</th>
                  <th className="px-4 py-3 text-right">Views</th>
                  <th className="px-4 py-3 text-right">Unique</th>
                  <th className="px-4 py-3 text-right">Today</th>
                  <th className="px-4 py-3 text-right">This week</th>
                </tr>
              </thead>
              <tbody>
                {analytics.top_posts.map((post) => (
                  <tr key={post.post_id} className="border-b last:border-0 hover:bg-muted/30">
                    <td className="max-w-[300px] truncate px-6 py-3 font-medium">
                      {post.title || post.post_id}
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">{post.total_views}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{post.unique_visitors}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{post.views_today}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{post.views_this_week}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center px-6 py-12 text-center text-sm text-muted-foreground">
            <Eye className="mb-2 h-8 w-8 opacity-40" />
            <p>No analytics data yet</p>
            <p className="text-xs">Page views will appear after readers visit your published blog posts.</p>
          </div>
        )}
      </div>
    </div>
  );
}
