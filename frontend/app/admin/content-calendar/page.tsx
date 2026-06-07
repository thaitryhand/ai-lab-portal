import { headers } from "next/headers";

import { AdminBackLink } from "@/components/admin/admin-back-link";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { cn } from "@/lib/utils";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

// ── Types ───────────────────────────────────────────────────────

type CalendarPost = {
  id: string;
  title: string;
  slug?: string;
  type: "post" | "idea";
  status: string;
  date?: string | null;
  stage?: string;
  created_at?: string;
};

type CalendarData = {
  published: CalendarPost[];
  pipeline: CalendarPost[];
  month_counts: Record<string, number>;
};

async function getCalendarData(): Promise<CalendarData> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session?.user?.id) {
    return { published: [], pipeline: [], month_counts: {} };
  }

  const response = await fetch(
    `${backendBaseUrl}/admin/content-calendar/posts`,
    {
      headers: createAdminBoundaryHeaders({
        user: { id: session.user.id, email: session.user.email },
      }),
      cache: "no-store",
    },
  );

  if (!response.ok) return { published: [], pipeline: [], month_counts: {} };
  return response.json();
}

// ── Calendar helpers ──────────────────────────────────────────────

function getMonthDays(year: number, month: number) {
  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const days: (number | null)[] = [];

  // Pad start of week
  for (let i = 0; i < firstDay.getDay(); i++) {
    days.push(null);
  }

  for (let d = 1; d <= lastDay.getDate(); d++) {
    days.push(d);
  }

  return days;
}

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const DAY_HEADERS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function stageBadge(stage: string | undefined) {
  const colors: Record<string, string> = {
    published: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    marketing_done: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
    reviewed: "bg-purple-500/10 text-purple-600 dark:text-purple-400",
    draft_done: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
    outline_done: "bg-brand/10 text-brand",
    approved: "bg-muted text-muted-foreground",
    idea: "bg-muted/50 text-muted-foreground",
  };
  const label: Record<string, string> = {
    published: "Published",
    marketing_done: "Marketing",
    reviewed: "Reviewed",
    draft_done: "Draft",
    outline_done: "Outline",
    approved: "Approved",
    idea: "Idea",
  };
  return (
    <span
      className={cn(
        "inline-block rounded px-1.5 py-0.5 text-[10px] font-medium",
        colors[stage ?? "idea"] ?? "bg-muted text-muted-foreground",
      )}
    >
      {label[stage ?? "idea"] ?? stage}
    </span>
  );
}

// ── Calendar Grid ─────────────────────────────────────────────────

function CalendarGrid({
  year,
  month,
  postsByDate,
}: {
  year: number;
  month: number;
  postsByDate: Map<string, CalendarPost[]>;
}) {
  const days = getMonthDays(year, month);
  const today = new Date();
  const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

  return (
    <div className="rounded-xl border border-border/60 bg-card overflow-hidden">
      {/* Day headers */}
      <div className="grid grid-cols-7 border-b border-border/60">
        {DAY_HEADERS.map((d) => (
          <div
            key={d}
            className="px-2 py-2 text-center text-[11px] font-semibold text-muted-foreground uppercase tracking-wider border-r border-border/30 last:border-r-0"
          >
            {d}
          </div>
        ))}
      </div>

      {/* Day cells */}
      <div className="grid grid-cols-7">
        {days.map((day, idx) => {
          if (day === null) {
            return <div key={`empty-${idx}`} className="min-h-[100px] border-r border-b border-border/30 last:border-r-0 bg-muted/20" />;
          }

          const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          const dayPosts = postsByDate.get(dateStr) ?? [];
          const isToday = dateStr === todayStr;

          return (
            <div
              key={dateStr}
              className={cn(
                "min-h-[100px] p-1.5 border-r border-b border-border/30 last:border-r-0 relative",
                isToday && "bg-brand/[0.03]",
              )}
            >
              <span
                className={cn(
                  "inline-flex items-center justify-center w-6 h-6 text-xs font-medium rounded-full",
                  isToday && "bg-brand text-white",
                  !isToday && "text-muted-foreground",
                )}
              >
                {day}
              </span>
              <div className="mt-0.5 space-y-0.5">
                {dayPosts.slice(0, 3).map((post) => (
                  <a
                    key={post.id}
                    href={
                      post.type === "post" && post.slug
                        ? `/blog/${post.slug}`
                        : `/admin/blog-ideas/${post.id}`
                    }
                    className={cn(
                      "block truncate rounded px-1 py-0.5 text-[10px] leading-tight transition-colors",
                      post.type === "post"
                        ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/20"
                        : "bg-amber-500/10 text-amber-700 dark:text-amber-300 hover:bg-amber-500/20",
                    )}
                  >
                    {post.title}
                  </a>
                ))}
                {dayPosts.length > 3 && (
                  <span className="text-[10px] text-muted-foreground block px-1">
                    +{dayPosts.length - 3} more
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────

export default async function ContentCalendarPage() {
  const data = await getCalendarData();
  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth();

  // Group published posts by date
  const postsByDate = new Map<string, CalendarPost[]>();
  for (const post of data.published) {
    if (post.date) {
      const dateKey = post.date.slice(0, 10);
      const existing = postsByDate.get(dateKey) ?? [];
      existing.push(post);
      postsByDate.set(dateKey, existing);
    }
  }

  // Pipeline stats
  const publishedCount = data.published.length;
  const inProgress = data.pipeline.filter(
    (p) => p.stage && p.stage !== "published",
  ).length;
  const ideas = data.pipeline.length;

  return (
    <div className={adminPageStackClass}>
      <AdminPageHeader
        title="Content Calendar"
        description="Blog post schedule and pipeline overview"
        actions={<AdminBackLink href="/admin">Back to dashboard</AdminBackLink>}
      />

      {/* Stat cards */}
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-border/60 bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground mb-1">
            Published
          </p>
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
            {publishedCount}
          </p>
        </div>
        <div className="rounded-xl border border-border/60 bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground mb-1">
            In Pipeline
          </p>
          <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
            {inProgress}
          </p>
        </div>
        <div className="rounded-xl border border-border/60 bg-card p-4">
          <p className="text-xs font-medium text-muted-foreground mb-1">
            Total Ideas
          </p>
          <p className="text-2xl font-bold text-foreground">{ideas}</p>
        </div>
      </div>

      {/* Month label */}
      <h2 className="text-lg font-semibold">
        {MONTHS[currentMonth]} {currentYear}
      </h2>

      {/* Calendar grid */}
      <CalendarGrid
        year={currentYear}
        month={currentMonth}
        postsByDate={postsByDate}
      />

      {/* Pipeline ideas */}
      {data.pipeline.length > 0 && (
        <div className="rounded-xl border border-border/60 bg-card p-4">
          <h2 className="text-sm font-semibold mb-3">Pipeline Ideas</h2>
          <div className="space-y-2">
            {data.pipeline.map((idea) => (
              <a
                key={idea.id}
                href={`/admin/blog-ideas/${idea.id}`}
                className="flex items-center gap-3 rounded-lg border border-border/30 p-3 transition-colors hover:bg-muted/50"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{idea.title}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Created{" "}
                    {new Date(idea.created_at ?? "").toLocaleDateString()}
                  </p>
                </div>
                {stageBadge(idea.stage)}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
