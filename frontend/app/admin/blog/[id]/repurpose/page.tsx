import { headers } from "next/headers";
import { notFound, redirect } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { AdminDashboardHeader } from "@/components/admin/admin-dashboard-header";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { auth } from "@/lib/auth/server";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { RepurposeClient } from "./repurpose-client";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type BlogPostDetail = {
  id: string;
  slug: string;
  title: string;
  excerpt: string;
  status: string;
  published_at: string | null;
};

type RepurposedContent = {
  id: string;
  blog_post_id: string;
  twitter_thread: {
    tweets: Array<{ number: number; content: string }>;
  } | null;
  linkedin_article: {
    headline: string;
    summary: string;
    key_takeaways: string[];
  } | null;
  summary_snippet: string;
  created_at: string;
};

async function fetchPost(postId: string): Promise<BlogPostDetail | null> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return null;

  try {
    const res = await fetch(`${backendBaseUrl}/admin/blog-posts/${postId}`, {
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

async function fetchRepurposedContent(postId: string): Promise<RepurposedContent | null> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return null;

  try {
    const res = await fetch(`${backendBaseUrl}/admin/blog-posts/${postId}/repurpose`, {
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

export default async function RepurposePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const post = await fetchPost(id);
  if (!post) notFound();
  if (post.status !== "published") {
    return (
      <div className={adminPageStackClass}>
        <AdminDashboardHeader
          title="Repurpose Content"
          description="This post must be published before it can be repurposed."
          email={session.user.email}
        />
        <a
          href={`/admin/blog/${id}/edit`}
          className="inline-flex items-center gap-1.5 text-sm text-brand hover:underline"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to editor
        </a>
      </div>
    );
  }

  const content = await fetchRepurposedContent(id);

  return (
    <div className={adminPageStackClass}>
      <AdminDashboardHeader
        title={`Repurpose: ${post.title}`}
        description="Generate social media content from this blog post."
        email={session.user.email}
      />
      <a
        href="/admin/blog"
        className="-mt-2 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to blog posts
      </a>

      {!content ? (
        <div className="flex flex-col items-center justify-center rounded-lg border bg-card px-6 py-16 text-center text-sm text-muted-foreground">
          <p>Failed to generate repurposed content.</p>
        </div>
      ) : (
        <RepurposeClient content={content} />
      )}
    </div>
  );
}
