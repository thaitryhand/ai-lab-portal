import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type SessionUser = { id: string; email: string };

export type AdminDashboardStats = {
  blogDrafts: number;
  blogPublished: number;
  blogTotal: number;
  ideasPending: number;
  ideasApproved: number;
  ideasTotal: number;
  showcasesDrafts: number;
  showcasesPublished: number;
  showcasesTotal: number;
  projectsDrafts: number;
  projectsPublished: number;
  projectsTotal: number;
  newsPublished: number;
  commentsTotal: number;
  recentActivity: Array<{
    action: string;
    actorEmail: string;
    createdAt: string;
  }>;
};

type BackendStatsResponse = {
  blog_drafts: number;
  blog_published: number;
  blog_total: number;
  ideas_pending: number;
  ideas_approved: number;
  ideas_total: number;
  showcases_drafts: number;
  showcases_published: number;
  showcases_total: number;
  projects_drafts: number;
  projects_published: number;
  projects_total: number;
  news_published: number;
  comments_total: number;
  recent_activity: Array<{
    action: string;
    actor_email: string;
    created_at: string;
  }>;
};

function snakeToCamel(src: BackendStatsResponse): AdminDashboardStats {
  return {
    blogDrafts: src.blog_drafts,
    blogPublished: src.blog_published,
    blogTotal: src.blog_total,
    ideasPending: src.ideas_pending,
    ideasApproved: src.ideas_approved,
    ideasTotal: src.ideas_total,
    showcasesDrafts: src.showcases_drafts,
    showcasesPublished: src.showcases_published,
    showcasesTotal: src.showcases_total,
    projectsDrafts: src.projects_drafts,
    projectsPublished: src.projects_published,
    projectsTotal: src.projects_total,
    newsPublished: src.news_published,
    commentsTotal: src.comments_total,
    recentActivity: src.recent_activity.map((e) => ({
      action: e.action,
      actorEmail: e.actor_email,
      createdAt: e.created_at,
    })),
  };
}

export async function fetchAdminDashboardStats(user: SessionUser): Promise<AdminDashboardStats> {
  // Try unified endpoint first
  try {
    const response = await fetch(`${backendBaseUrl}/admin/dashboard/stats`, {
      headers: createAdminBoundaryHeaders({ user }),
      cache: "no-store",
    });

    if (response.ok) {
      const data = (await response.json()) as BackendStatsResponse;
      return snakeToCamel(data);
    }
  } catch {
    // fall through to per-endpoint fallback
  }

  // Fallback: fetch each collection individually
  type BlogPostRow = { status: "draft" | "published" };
  type ShowcaseRow = { status: "draft" | "published" };
  type IdeaRow = { status: "pending" | "approved" | "rejected" };

  async function fetchJson<T>(path: string): Promise<T[]> {
    try {
      const response = await fetch(`${backendBaseUrl}${path}`, {
        headers: createAdminBoundaryHeaders({ user }),
        cache: "no-store",
      });
      if (!response.ok) return [];
      return (await response.json()) as T[];
    } catch {
      return [];
    }
  }

  const [posts, showcases, ideas] = await Promise.all([
    fetchJson<BlogPostRow>("/admin/blog-posts"),
    fetchJson<ShowcaseRow>("/admin/showcases"),
    fetchJson<IdeaRow>("/admin/blog-ideas"),
  ]);

  const blogPublished = posts.filter((p) => p.status === "published").length;
  const showcasesPublished = showcases.filter((s) => s.status === "published").length;

  return {
    blogDrafts: posts.length - blogPublished,
    blogPublished,
    blogTotal: posts.length,
    ideasPending: ideas.filter((i) => i.status === "pending").length,
    ideasApproved: ideas.filter((i) => i.status === "approved").length,
    ideasTotal: ideas.length,
    showcasesDrafts: showcases.length - showcasesPublished,
    showcasesPublished,
    showcasesTotal: showcases.length,
    projectsDrafts: 0,
    projectsPublished: 0,
    projectsTotal: 0,
    newsPublished: 0,
    commentsTotal: 0,
    recentActivity: [],
  };
}
