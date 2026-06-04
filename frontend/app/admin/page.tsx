import { headers } from "next/headers";
import { redirect } from "next/navigation";
import {
  Briefcase,
  FileText,
  Lightbulb,
  PencilLine,
  Shield,
  Sparkles,
  Newspaper,
  Rss,
} from "lucide-react";

import { AdminCmsShell } from "@/components/admin/admin-cms-shell";
import { AdminDashboardHeader } from "@/components/admin/admin-dashboard-header";
import { AdminDashboardStatGrid } from "@/components/admin/admin-dashboard-stat-grid";
import { AdminModuleCard, type AdminModuleCardProps } from "@/components/admin/admin-module-card";
import {
  adminCardClass,
  adminPageStackClass,
  adminSectionPanelClass,
  adminSectionTitleClass,
} from "@/components/admin/admin-ui";
import { auth } from "@/lib/auth/server";
import { fetchAdminDashboardStats } from "@/lib/admin/fetch-dashboard-stats";
import { cn } from "@/lib/utils";

const liveModules: AdminModuleCardProps[] = [
  {
    title: "Blog posts",
    description: "Review drafts, publish articles, and manage the editorial library.",
    href: "/admin/blog",
    icon: FileText,
    status: "live",
  },
  {
    title: "Compose",
    description: "Open the Tiptap workspace for a new article or quick edits.",
    href: "/admin/blog/editor",
    icon: PencilLine,
    status: "live",
  },
  {
    title: "Blog ideas",
    description: "Approve angles, generate outlines, and route drafts through the pipeline.",
    href: "/admin/blog-ideas",
    icon: Lightbulb,
    status: "live",
  },
  {
    title: "Projects",
    description: "Showcase company projects and internal tools with full CRUD workflow.",
    href: "/admin/projects",
    icon: Briefcase,
    status: "live",
  },
  {
    title: "Showcases",
    description: "Publish client-ready delivery stories with industry metadata.",
    href: "/admin/showcases",
    icon: Briefcase,
    status: "live",
  },
  {
    title: "AI News review",
    description: "Approve, reject, and publish scored intelligence candidates.",
    href: "/admin/news-review",
    icon: Newspaper,
    status: "live",
  },
  {
    title: "AI News sources",
    description: "Configure RSS and official feeds for the intelligence pipeline.",
    href: "/admin/news-sources",
    icon: Rss,
    status: "live",
  },
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
    { label: "Blog ideas", value: stats.ideasTotal, hint: `${stats.ideasPending} pending, ${stats.ideasApproved} approved`, href: "/admin/blog-ideas", icon: Lightbulb },
    { label: "Showcases", value: stats.showcasesTotal, hint: `${stats.showcasesPublished} live, ${stats.showcasesDrafts} drafts`, href: "/admin/showcases", icon: Briefcase },
    { label: "AI News", value: stats.newsPublished, hint: "published items", href: "/admin/news-review", icon: Newspaper },
  ];

  return (
    <AdminCmsShell active="dashboard">
      <div className={adminPageStackClass}>
        <AdminDashboardHeader
          description="A calmer publishing cockpit for reviewing ideas, drafting articles, and keeping public content intentional."
          email={session.user.email}
          title="Operations dashboard"
        />

        <AdminDashboardStatGrid stats={statCards} />

        {stats.recentActivity.length > 0 && (
          <section className={adminSectionPanelClass}>
            <div className="border-b border-border px-4 py-4 sm:px-5">
              <h2 className={adminSectionTitleClass}>Recent activity</h2>
              <p className="mt-1 text-sm text-muted-foreground">
                Latest editorial actions across the system.
              </p>
            </div>
            <div className="divide-y divide-border">
              {stats.recentActivity.slice(0, 8).map((event, i) => (
                <div key={i} className="flex items-center justify-between px-4 py-3 text-sm sm:px-5">
                  <span className="text-foreground">{event.action}</span>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {event.actorEmail}
                    <span className="ml-2">{new Date(event.createdAt).toLocaleString()}</span>
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        <section className={adminSectionPanelClass}>
          <div className="grid gap-3 border-b border-border px-4 py-4 sm:px-5 lg:grid-cols-[minmax(0,1fr)_14rem] lg:items-end">
            <div>
              <h2 className={adminSectionTitleClass}>Live workflows</h2>
              <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
                Everything here is wired to the FastAPI admin boundary today.
              </p>
            </div>
            <p className="rounded-md border border-border bg-muted/25 p-3 text-xs leading-relaxed text-muted-foreground">
              Pick a workflow, make the smallest editorial move, then return here to scan the system.
            </p>
          </div>
          <div className="grid gap-2 p-3 sm:grid-cols-2 sm:p-4">
            {liveModules.map((module) => (
              <AdminModuleCard key={module.title} {...module} />
            ))}
          </div>
        </section>

        <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_16rem]">
          <div className={cn(adminCardClass, "p-4")}>
            <h2 className={adminSectionTitleClass}>Roadmap parking lot</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Visible, but deliberately separate from what can be used today.
            </p>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {plannedModules.map((module) => (
                <AdminModuleCard key={module.title} {...module} />
              ))}
            </div>
          </div>

          <div className={cn(adminCardClass, "p-4")}>
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-accent text-brand">
              <Shield className="size-4" aria-hidden />
            </span>
            <h2 className={cn(adminSectionTitleClass, "mt-3")}>Human review stays in the loop</h2>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              Roles, provider workflows, and automated drafting arrive in later story slices. Today this shell keeps publishing deliberate and inspectable.
            </p>
          </div>
        </section>
      </div>
    </AdminCmsShell>
  );
}
