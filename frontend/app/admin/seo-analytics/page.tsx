import { headers } from "next/headers";
import { redirect } from "next/navigation";
import {
  AlertTriangle,
  BarChart3,
  Hash,
  Newspaper,
  Search,
  Sparkles,
  Tag,
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

type SeoStats = {
  total_posts: number;
  published_posts: number;
  draft_posts: number;
  ideas_with_seo: number;
  avg_seo_score: number;
  total_seo_issues: number;
  posts_needing_attention: number;
  publish_trend: Record<string, number>;
  tags: number;
};

type SeoPostAnalysis = {
  post_id: string;
  title: string;
  slug: string;
  status: string;
  published_at: string | null;
  seo_score: number;
  issues: string[];
  seo_details: {
    seo_title_length: number;
    meta_description_length: number;
    keyword_count: number;
  };
  has_marketing_metadata: boolean;
};

type KeywordItem = {
  name: string;
  count: number;
  type: "tag" | "keyword";
};

/* ── Data fetching ── */

async function fetchSeoStats(): Promise<SeoStats | null> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return null;

  try {
    const res = await fetch(`${backendBaseUrl}/admin/seo-analytics/stats`, {
      headers: createAdminBoundaryHeaders({
        user: { id: session.user.id, email: session.user.email },
      }),
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

async function fetchSeoPosts(): Promise<SeoPostAnalysis[]> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return [];

  try {
    const res = await fetch(`${backendBaseUrl}/admin/seo-analytics/posts`, {
      headers: createAdminBoundaryHeaders({
        user: { id: session.user.id, email: session.user.email },
      }),
      cache: "no-store",
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

async function fetchKeywords(): Promise<KeywordItem[]> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return [];

  try {
    const res = await fetch(`${backendBaseUrl}/admin/seo-analytics/keywords`, {
      headers: createAdminBoundaryHeaders({
        user: { id: session.user.id, email: session.user.email },
      }),
      cache: "no-store",
    });
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

/* ── Sub-components ── */

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 80
      ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
      : score >= 50
        ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
        : "bg-red-500/10 text-red-600 dark:text-red-400";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold",
        color,
      )}
    >
      <Search className="size-3" />
      {score}
    </span>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  hint,
}: {
  icon: typeof BarChart3;
  label: string;
  value: string | number;
  hint?: string;
}) {
  return (
    <div className="rounded-xl border border-border/60 bg-card p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-1">
            {label}
          </p>
          <p className="text-2xl font-bold text-foreground">{value}</p>
          {hint && (
            <p className="text-xs text-muted-foreground mt-1">{hint}</p>
          )}
        </div>
        <span className="rounded-lg border border-border/40 bg-muted/30 p-2 text-muted-foreground">
          <Icon className="size-4" />
        </span>
      </div>
    </div>
  );
}

function TrendChart({ trend }: { trend: Record<string, number> }) {
  const entries = Object.entries(trend).sort(([a], [b]) => a.localeCompare(b));
  const maxVal = Math.max(...Object.values(trend), 1);
  const reversedMonths = entries.slice(-12);

  return (
    <div className="rounded-xl border border-border/60 bg-card p-4">
      <h3 className="text-sm font-semibold mb-4">Publish Trend</h3>
      <div className="flex items-end gap-1.5 h-32">
        {reversedMonths.map(([month, count]) => {
          const height = (count / maxVal) * 100;
          const [y, m] = month.split("-");
          const label = new Date(Number(y), Number(m) - 1).toLocaleDateString(
            "en-US",
            { month: "short" },
          );
          return (
            <div key={month} className="flex-1 flex flex-col items-center gap-1">
              <span className="text-[10px] text-muted-foreground">{count}</span>
              <div
                className="w-full rounded-t bg-brand/60 transition-all hover:bg-brand"
                style={{ height: `${Math.max(height, 2)}%` }}
              />
              <span className="text-[9px] text-muted-foreground">{label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PostTable({ posts }: { posts: SeoPostAnalysis[] }) {
  if (posts.length === 0) {
    return (
      <div className="rounded-xl border border-border/60 bg-card p-8 text-center text-sm text-muted-foreground">
        No SEO data yet. Publish posts with marketing metadata to see analysis.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-border/60 bg-card">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border/60 text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <th className="px-4 py-3">Post</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">SEO Score</th>
            <th className="px-4 py-3">Issues</th>
            <th className="px-4 py-3">Title / Meta</th>
          </tr>
        </thead>
        <tbody>
          {posts.map((post, i) => (
            <tr
              key={post.post_id}
              className={cn(
                "border-b border-border/30 transition-colors hover:bg-muted/30",
                i === posts.length - 1 && "border-b-0",
              )}
            >
              <td className="px-4 py-3">
                <a
                  href={
                    post.status === "published"
                      ? `/blog/${post.slug}`
                      : `/admin/blog/editor?slug=${post.slug}`
                  }
                  className="font-medium text-foreground hover:text-brand transition-colors"
                >
                  {post.title}
                </a>
              </td>
              <td className="px-4 py-3">
                <span
                  className={cn(
                    "rounded px-1.5 py-0.5 text-[10px] font-medium",
                    post.status === "published"
                      ? "bg-emerald-500/10 text-emerald-600"
                      : "bg-amber-500/10 text-amber-600",
                  )}
                >
                  {post.status}
                </span>
              </td>
              <td className="px-4 py-3">
                <ScoreBadge score={post.seo_score} />
              </td>
              <td className="px-4 py-3">
                {post.issues.length > 0 ? (
                  <ul className="space-y-0.5">
                    {post.issues.slice(0, 2).map((issue, j) => (
                      <li
                        key={j}
                        className="flex items-center gap-1 text-[11px] text-red-600 dark:text-red-400"
                      >
                        <AlertTriangle className="size-3 shrink-0" />
                        <span className="truncate max-w-[200px]">{issue}</span>
                      </li>
                    ))}
                    {post.issues.length > 2 && (
                      <li className="text-[10px] text-muted-foreground pl-4">
                        +{post.issues.length - 2} more
                      </li>
                    )}
                  </ul>
                ) : (
                  <span className="text-xs text-muted-foreground">None</span>
                )}
              </td>
              <td className="px-4 py-3 text-[11px] text-muted-foreground">
                {post.has_marketing_metadata ? (
                  <div>
                    <span
                      className={cn(
                        post.seo_details.seo_title_length > 0 &&
                          post.seo_details.seo_title_length <= 60
                          ? "text-emerald-600"
                          : "text-red-600",
                      )}
                    >
                      Title: {post.seo_details.seo_title_length}c
                    </span>
                    <span className="mx-1">·</span>
                    <span
                      className={cn(
                        post.seo_details.meta_description_length > 0 &&
                          post.seo_details.meta_description_length <= 160
                          ? "text-emerald-600"
                          : "text-red-600",
                      )}
                    >
                      Meta: {post.seo_details.meta_description_length}c
                    </span>
                    <span className="mx-1">·</span>
                    <span>KW: {post.seo_details.keyword_count}</span>
                  </div>
                ) : (
                  <span className="text-red-600">No metadata</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function KeywordCloud({ items }: { items: KeywordItem[] }) {
  if (items.length === 0) {
    return (
      <div className="rounded-xl border border-border/60 bg-card p-8 text-center text-sm text-muted-foreground">
        No keywords or tags found.
      </div>
    );
  }

  const maxCount = Math.max(...items.map((k) => k.count), 1);

  return (
    <div className="rounded-xl border border-border/60 bg-card p-4">
      <h3 className="text-sm font-semibold mb-4">Keywords & Tags</h3>
      <div className="flex flex-wrap gap-2">
        {items.slice(0, 30).map((item) => {
          const size =
            item.count / maxCount > 0.66
              ? "text-sm font-semibold"
              : item.count / maxCount > 0.33
                ? "text-xs font-medium"
                : "text-[11px]";
          return (
            <span
              key={`${item.type}-${item.name}`}
              className={cn(
                "inline-flex items-center gap-1 rounded-full px-2.5 py-1 transition-colors",
                item.type === "tag"
                  ? "bg-brand/8 text-brand hover:bg-brand/15"
                  : "bg-muted/50 text-muted-foreground hover:bg-muted",
                size,
              )}
            >
              {item.type === "tag" ? (
                <Tag className="size-3" />
              ) : (
                <Hash className="size-3" />
              )}
              {item.name}
              <span className="text-[10px] opacity-60">({item.count})</span>
            </span>
          );
        })}
      </div>
    </div>
  );
}

/* ── Page ── */

export default async function SeoAnalyticsPage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const [stats, posts, keywords] = await Promise.all([
    fetchSeoStats(),
    fetchSeoPosts(),
    fetchKeywords(),
  ]);

  return (
    <div className={adminPageStackClass}>
      <AdminPageHeader
        title="SEO Analytics"
        description="Blog post SEO performance, keyword analysis, and optimization insights"
        actions={<AdminBackLink href="/admin">Back to dashboard</AdminBackLink>}
      />

      {/* Stats grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={Newspaper}
          label="Published Posts"
          value={stats?.published_posts ?? 0}
        />
        <StatCard
          icon={Sparkles}
          label="Avg SEO Score"
          value={stats ? `${stats.avg_seo_score}/100` : "—"}
          hint={
            stats?.posts_needing_attention
              ? `${stats.posts_needing_attention} need attention`
              : undefined
          }
        />
        <StatCard
          icon={AlertTriangle}
          label="SEO Issues"
          value={stats?.total_seo_issues ?? 0}
          hint={
            stats?.ideas_with_seo
              ? `Across ${stats.ideas_with_seo} ideas`
              : undefined
          }
        />
        <StatCard
          icon={Tag}
          label="Tags"
          value={stats?.tags ?? 0}
        />
      </div>

      {/* Trend chart + Keywords */}
      <div className="grid gap-6 lg:grid-cols-2">
        {stats?.publish_trend && (
          <TrendChart trend={stats.publish_trend} />
        )}
        <KeywordCloud items={keywords} />
      </div>

      {/* Per-post analysis */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold">Per-Post SEO Analysis</h2>
          <span className="text-xs text-muted-foreground">
            Sorted by score (lowest first)
          </span>
        </div>
        <PostTable posts={posts} />
      </div>
    </div>
  );
}
