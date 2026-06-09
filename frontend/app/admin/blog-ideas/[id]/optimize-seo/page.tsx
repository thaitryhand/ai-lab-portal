import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { ArrowLeft, Sparkles } from "lucide-react";

import { AdminDashboardHeader } from "@/components/admin/admin-dashboard-header";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { auth } from "@/lib/auth/server";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type SeoChange = {
  section: string;
  before: string;
  after: string;
  rationale: string;
};

type SeoOptimizationResult = {
  id: string;
  blog_idea_id: string;
  changes: SeoChange[];
  overall_summary: string;
  created_at: string;
};

async function fetchOptimization(ideaId: string): Promise<SeoOptimizationResult | null> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return null;

  try {
    const res = await fetch(`${backendBaseUrl}/admin/blog-ideas/${ideaId}/optimize-seo`, {
      method: "POST",
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

const sectionLabels: Record<string, string> = {
  title: "Title",
  meta_description: "Meta Description",
  headings: "Heading Structure",
  internal_links: "Internal Links",
  keywords: "Keyword Placement",
};

export default async function OptimizeSeoPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const result = await fetchOptimization(id);

  if (!result) {
    return (
      <div className={adminPageStackClass}>
        <AdminDashboardHeader
          title="SEO Optimization"
          description="Could not generate optimization suggestions."
          email={session.user.email}
        />
        <a
          href={`/admin/blog-ideas/${id}`}
          className="inline-flex items-center gap-1.5 text-sm text-brand hover:underline"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to idea
        </a>
      </div>
    );
  }

  return (
    <div className={adminPageStackClass}>
      <AdminDashboardHeader
        title="SEO Optimization Results"
        description={result.overall_summary}
        email={session.user.email}
      />
      <a
        href={`/admin/blog-ideas/${id}`}
        className="-mt-2 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to idea
      </a>

      <div className="space-y-4">
        {result.changes.map((change, i) => (
          <div key={i} className="rounded-lg border bg-card p-6 text-card-foreground shadow-sm">
            <div className="mb-4 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-brand" />
              <h3 className="text-sm font-semibold">
                {sectionLabels[change.section] || change.section}
              </h3>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-red-200 bg-red-50/50 p-4 dark:border-red-900/30 dark:bg-red-950/10">
                <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-red-600 dark:text-red-400">
                  Before
                </p>
                <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                  {change.before || <span className="italic opacity-50">(empty)</span>}
                </p>
              </div>
              <div className="rounded-lg border border-emerald-200 bg-emerald-50/50 p-4 dark:border-emerald-900/30 dark:bg-emerald-950/10">
                <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                  After
                </p>
                <p className="whitespace-pre-wrap text-sm text-foreground">
                  {change.after}
                </p>
              </div>
            </div>

            <p className="mt-3 text-xs italic text-muted-foreground">
              {change.rationale}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
