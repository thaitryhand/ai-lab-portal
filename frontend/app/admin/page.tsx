import { headers } from "next/headers";
import { redirect } from "next/navigation";
import {
  Activity,
  BarChart3,
  Briefcase,
  Calendar,
  FileText,
  GitBranch,
  Lightbulb,
  MessageSquare,
  Newspaper,
  PencilLine,
  Play,
  Rss,
  Search,
  Shield,
  Sparkles,
} from "lucide-react";

import { AdminDashboardHeader } from "@/components/admin/admin-dashboard-header";
import { AdminDashboardStatGrid } from "@/components/admin/admin-dashboard-stat-grid";
import { AdminModuleCard, type AdminModuleCardProps } from "@/components/admin/admin-module-card";
import { AdminHealthWidget } from "@/components/admin/admin-health-widget";
import { adminPageStackClass } from "@/components/admin/admin-ui";

import { auth } from "@/lib/auth/server";
import { fetchAdminDashboardStats } from "@/lib/admin/fetch-dashboard-stats";

/* ── Module data ── */

const liveModules: AdminModuleCardProps[] = [
  { title: "Blog posts", description: "Review drafts, publish articles, and manage the editorial library.", href: "/admin/blog", icon: FileText, status: "live" },
  { title: "Compose", description: "Open the Tiptap workspace for a new article or quick edits.", href: "/admin/blog/editor", icon: PencilLine, status: "live" },
  { title: "Blog ideas", description: "Approve angles, generate outlines, and route drafts through the pipeline.", href: "/admin/blog-ideas", icon: Lightbulb, status: "live" },
  { title: "Projects", description: "Showcase company projects and internal tools with full CRUD workflow.", href: "/admin/projects", icon: Briefcase, status: "live" },
  { title: "Showcases", description: "Publish client-ready delivery stories with industry metadata.", href: "/admin/showcases", icon: Briefcase, status: "live" },
  { title: "AI News review", description: "Approve, reject, and publish scored intelligence candidates.", href: "/admin/news-review", icon: Newspaper, status: "live" },
  { title: "Content Calendar", description: "View published posts and pipeline ideas on a calendar.", href: "/admin/content-calendar", icon: Calendar, status: "live" },
  { title: "AI News sources", description: "Configure RSS and official feeds for the intelligence pipeline.", href: "/admin/news-sources", icon: Rss, status: "live" },
  { title: "Pipeline Dashboard", description: "Stage distribution, throughput, cycle time, and Gantt overview.", href: "/admin/pipeline-dashboard", icon: GitBranch, status: "live" },
  { title: "SEO Analytics", description: "SEO scores, keyword analysis, and per-post optimization insights.", href: "/admin/seo-analytics", icon: Search, status: "live" },
  { title: "Seed Studio", description: "Populate demo content for tours, blog, and showcases.", href: "/admin/seed-studio", icon: Sparkles, status: "live" },
  { title: "AI Observability", description: "Run metrics, latency, token usage, and AI cost tracking across pipeline stages.", href: "/admin/ai-observability", icon: Activity, status: "live" },
  { title: "Pipeline Runner", description: "Run the full seed pipeline: generate idea, auto-approve gates, and publish to blog.", href: "/admin/pipeline-runner", icon: Play, status: "live" },
];

const plannedModules: AdminModuleCardProps[] = [
  { title: "Editorial queue", description: "AI-assisted review queues and human approval routing.", icon: Sparkles, status: "planned" },
  { title: "Prompt registry", description: "Versioned prompts and provider configuration.", icon: Sparkles, status: "planned" },
];

/* ── Page ── */

export default async function AdminDashboardPage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const stats = await fetchAdminDashboardStats({
    id: session.user.id,
    email: session.user.email,
  });

  const statCards = [
    { label: "Blog posts", value: stats.blogTotal, hint: `${stats.blogPublished} live, ${stats.blogDrafts} drafts`, href: "/admin/blog", icon: FileText },
    { label: "Comments", value: stats.commentsTotal, hint: "across all posts", href: "/admin/blog-comments", icon: MessageSquare },
    { label: "Blog ideas", value: stats.ideasTotal, hint: `${stats.ideasPending} pending, ${stats.ideasApproved} approved`, href: "/admin/blog-ideas", icon: Lightbulb },
    { label: "Showcases", value: stats.showcasesTotal, hint: `${stats.showcasesPublished} live, ${stats.showcasesDrafts} drafts`, href: "/admin/showcases", icon: Briefcase },
    { label: "AI News", value: stats.newsPublished, hint: "published items", href: "/admin/news-review", icon: Newspaper },
  ];

  return (
    <div className={adminPageStackClass}>
      {/* ── Header ── */}
      <AdminDashboardHeader
        description="A calmer publishing cockpit for reviewing ideas, drafting articles, and keeping public content intentional."
        email={session.user.email}
        title="Operations dashboard"
      />

      {/* ── Stats at a glance ── */}
      <AdminDashboardStatGrid stats={statCards} />

      {/* ── Live workflows ── */}
      <section className="rounded-2xl border border-border/40 bg-card shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
        <div className="flex items-center gap-3 border-b border-border/30 px-6 py-4">
          <span className="flex size-7 items-center justify-center rounded-lg bg-green-500/10">
            <span className="size-2 rounded-full bg-green-500 shadow-[0_0_6px_rgba(80,179,58,0.3)]" aria-hidden />
          </span>
          <div>
            <h2 className="text-sm font-semibold text-foreground">
              Live workflows
            </h2>
            <p className="mt-px text-xs text-muted-foreground/70">
              Everything here is wired to the FastAPI admin boundary today.
            </p>
          </div>
        </div>
        <div className="grid gap-3 p-5 sm:grid-cols-2 xl:grid-cols-3 sm:p-6">
          {liveModules.map((module) => (
            <AdminModuleCard key={module.title} compact {...module} />
          ))}
        </div>
      </section>

      {/* ── Two-column bottom section ── */}
      <div className="grid gap-5 lg:grid-cols-[1fr_26rem]">
        {/* Left: Recent activity */}
        {stats.recentActivity.length > 0 ? (
          <section className="rounded-2xl border border-border/40 bg-card shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
            <div className="flex items-center gap-3 border-b border-border/30 px-6 py-4">
              <span className="flex size-7 items-center justify-center rounded-lg bg-muted/30">
                <Activity className="size-3.5 text-muted-foreground/70" aria-hidden />
              </span>
              <div>
                <h2 className="text-sm font-semibold text-foreground">
                  Recent activity
                </h2>
                <p className="mt-px text-xs text-muted-foreground/70">
                  Latest editorial actions.
                </p>
              </div>
            </div>
            <div className="divide-y divide-border/20">
              {stats.recentActivity.slice(0, 6).map((event, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between gap-3 px-6 py-3.5 text-sm transition-colors hover:bg-muted/5"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className="relative flex size-2 shrink-0">
                      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-500/30 opacity-75" />
                      <span className="relative inline-flex size-2 rounded-full bg-green-500" />
                    </span>
                    <span className="truncate text-foreground/80">
                      {event.action}
                    </span>
                  </div>
                  <span className="shrink-0 text-xs text-muted-foreground/50">
                    {new Date(event.createdAt).toLocaleDateString("en-US", {
                      month: "short",
                      day: "numeric",
                    })}
                  </span>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {/* Right column: Roadmap + Health + Human review */}
        <div className="flex flex-col gap-5">
          {/* Roadmap card */}
          <section className="rounded-2xl border border-border/40 bg-card shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
            <div className="flex items-center gap-3 border-b border-border/30 px-6 py-4">
              <span className="flex size-7 items-center justify-center rounded-lg bg-amber-500/10">
                <Sparkles className="size-3.5 text-amber-500" aria-hidden />
              </span>
              <div>
                <h2 className="text-sm font-semibold text-foreground">
                  Roadmap
                </h2>
                <p className="mt-px text-xs text-muted-foreground/70">
                  What&apos;s coming next
                </p>
              </div>
            </div>
            <div className="grid gap-2.5 p-5">
              {plannedModules.map((module) => (
                <AdminModuleCard key={module.title} compact {...module} />
              ))}
            </div>
          </section>

          {/* Health widget */}
          <AdminHealthWidget />

          {/* Human review card */}
          <section className="rounded-2xl border border-border/40 bg-card shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
            <div className="flex items-center gap-3 border-b border-border/30 px-6 py-4">
              <span className="flex size-7 items-center justify-center rounded-lg bg-blue-500/10">
                <Shield className="size-3.5 text-blue-500" aria-hidden />
              </span>
              <div>
                <h2 className="text-sm font-semibold text-foreground">
                  Human review
                </h2>
                <p className="mt-px text-xs text-muted-foreground/70">
                  Keeps publishing deliberate
                </p>
              </div>
            </div>
            <div className="px-6 py-5">
              <p className="text-sm leading-relaxed text-muted-foreground/80">
                Roles, provider workflows, and automated drafting arrive in
                later story slices. Today this shell keeps publishing deliberate
                and inspectable.
              </p>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
