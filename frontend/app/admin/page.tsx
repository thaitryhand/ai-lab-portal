import { headers } from "next/headers";
import { redirect } from "next/navigation";
import {
  Activity,
  ArrowUpRight,
  Briefcase,
  FileText,
  Lightbulb,
  MessageSquare,
  Newspaper,
  PencilLine,
  Rss,
  Shield,
  Sparkles,
} from "lucide-react";

import { AdminDashboardHeader } from "@/components/admin/admin-dashboard-header";
import { AdminDashboardStatGrid } from "@/components/admin/admin-dashboard-stat-grid";
import { AdminModuleCard, type AdminModuleCardProps } from "@/components/admin/admin-module-card";
import {
  adminCardClass,
  adminPageStackClass,
} from "@/components/admin/admin-ui";

import { auth } from "@/lib/auth/server";
import { fetchAdminDashboardStats } from "@/lib/admin/fetch-dashboard-stats";
import { cn } from "@/lib/utils";

const liveModules: AdminModuleCardProps[] = [
  { title: "Blog posts", description: "Review drafts, publish articles, and manage the editorial library.", href: "/admin/blog", icon: FileText, status: "live" },
  { title: "Compose", description: "Open the Tiptap workspace for a new article or quick edits.", href: "/admin/blog/editor", icon: PencilLine, status: "live" },
  { title: "Blog ideas", description: "Approve angles, generate outlines, and route drafts through the pipeline.", href: "/admin/blog-ideas", icon: Lightbulb, status: "live" },
  { title: "Projects", description: "Showcase company projects and internal tools with full CRUD workflow.", href: "/admin/projects", icon: Briefcase, status: "live" },
  { title: "Showcases", description: "Publish client-ready delivery stories with industry metadata.", href: "/admin/showcases", icon: Briefcase, status: "live" },
  { title: "AI News review", description: "Approve, reject, and publish scored intelligence candidates.", href: "/admin/news-review", icon: Newspaper, status: "live" },
  { title: "AI News sources", description: "Configure RSS and official feeds for the intelligence pipeline.", href: "/admin/news-sources", icon: Rss, status: "live" },
];

const plannedModules: AdminModuleCardProps[] = [
  { title: "Editorial queue", description: "AI-assisted review queues and human approval routing.", icon: Sparkles, status: "planned" },
  { title: "Prompt registry", description: "Versioned prompts and provider configuration.", icon: Sparkles, status: "planned" },
  { title: "Publishing checks", description: "Preflight SEO, link, and metadata validation.", icon: Sparkles, status: "planned" },
];

export default async function AdminDashboardPage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const stats = await fetchAdminDashboardStats({ id: session.user.id, email: session.user.email });

  const statCards = [
    { label: "Blog posts", value: stats.blogTotal, hint: `${stats.blogPublished} live, ${stats.blogDrafts} drafts`, href: "/admin/blog", icon: FileText },
    { label: "Comments", value: stats.commentsTotal, hint: "across all posts", href: "/admin/blog-comments", icon: MessageSquare },
    { label: "Blog ideas", value: stats.ideasTotal, hint: `${stats.ideasPending} pending, ${stats.ideasApproved} approved`, href: "/admin/blog-ideas", icon: Lightbulb },
    { label: "Showcases", value: stats.showcasesTotal, hint: `${stats.showcasesPublished} live, ${stats.showcasesDrafts} drafts`, href: "/admin/showcases", icon: Briefcase },
    { label: "AI News", value: stats.newsPublished, hint: "published items", href: "/admin/news-review", icon: Newspaper },
  ];

  return (
    <div className={adminPageStackClass}>
      <AdminDashboardHeader
        description="A calmer publishing cockpit for reviewing ideas, drafting articles, and keeping public content intentional."
        email={session.user.email}
        title="Operations dashboard"
      />

      <AdminDashboardStatGrid stats={statCards} />

      {/* ── Live workflows ── */}
      <section className="rounded-[var(--radius-admin-md)] border border-border/60 bg-card shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
        <div className="border-b border-border/50 px-5 py-3.5">
          <h2 className="text-sm font-semibold text-foreground">Live workflows</h2>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Everything here is wired to the FastAPI admin boundary today.
          </p>
        </div>
        <div className="grid gap-2 p-3.5 sm:grid-cols-2 xl:grid-cols-3 sm:p-4">
          {liveModules.map((module) => (
            <AdminModuleCard key={module.title} compact {...module} />
          ))}
        </div>
      </section>

      {/* ── Recent activity + Roadmap ⎯ side by side ── */}
      <div className="grid gap-5 lg:grid-cols-[1fr_22rem]">
        {/* Recent activity */}
        {stats.recentActivity.length > 0 ? (
          <section className={cn(adminCardClass, "flex flex-col")}>
            <div className="flex items-center gap-2.5 border-b border-border/50 px-5 py-4">
              <Activity className="size-4 text-muted-foreground" aria-hidden />
              <div>
                <h2 className="text-sm font-semibold text-foreground">Recent activity</h2>
                <p className="mt-px text-sm text-muted-foreground">Latest editorial actions.</p>
              </div>
            </div>
            <div className="flex-1 divide-y divide-border/30">
              {stats.recentActivity.slice(0, 6).map((event, i) => (
                <div key={i} className="flex items-center justify-between gap-3 px-5 py-3 text-sm transition-colors hover:bg-muted/10">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="size-1.5 shrink-0 rounded-full bg-brand/60" aria-hidden />
                    <span className="truncate text-foreground">{event.action}</span>
                  </div>
                  <span className="shrink-0 text-xs text-muted-foreground/70">
                    {new Date(event.createdAt).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                  </span>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        {/* Right column: Roadmap + Human review */}
        <div className="flex flex-col gap-5">
          <div className={cn(adminCardClass, "p-5")}>
            <div className="flex items-center gap-2.5">
              <span className="flex size-8 items-center justify-center rounded-[var(--radius-admin-sm)] bg-accent text-brand ring-1 ring-brand/10">
                <Sparkles className="size-4" aria-hidden />
              </span>
              <div>
                <h2 className="text-sm font-semibold text-foreground">Roadmap</h2>
                <p className="mt-px text-xs text-muted-foreground">What&apos;s coming next</p>
              </div>
            </div>
            <div className="mt-4 grid gap-2.5">
              {plannedModules.map((module) => (
                <AdminModuleCard key={module.title} {...module} />
              ))}
            </div>
          </div>

          <div className={cn(adminCardClass, "p-5")}>
            <div className="flex items-center gap-2.5">
              <span className="flex size-8 items-center justify-center rounded-[var(--radius-admin-sm)] bg-accent text-brand ring-1 ring-brand/10">
                <Shield className="size-4" aria-hidden />
              </span>
              <div>
                <h2 className="text-sm font-semibold text-foreground">Human review</h2>
                <p className="mt-px text-xs text-muted-foreground">Keeps publishing deliberate</p>
              </div>
            </div>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
              Roles, provider workflows, and automated drafting arrive in later story slices. Today this shell keeps publishing deliberate and inspectable.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
