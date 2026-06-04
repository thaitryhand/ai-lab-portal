import { headers } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { AdminCmsShell } from "@/components/admin/admin-cms-shell";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { GenerationJobPoller } from "../generation-job-poller";
import { BlogIdeaDetailView, type BlogIdeaDetail, type BlogClaimItem } from "../idea-detail-view";
import {
  approveOutlineAction,
  rejectOutlineAction,
  generateOutlineAction,
  generateDraftAction,
  approveDraftAction,
  rejectDraftAction,
  reviewTechnicalAction,
  approveReviewAction,
  rejectReviewAction,
  generateMarketingAction,
  approveMarketingAction,
  rejectMarketingAction,
  publishToBlogAction,
  extractClaimsAction,
  updateClaimAction,
} from "../actions";


const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

async function getBlogIdea(id: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}/admin/blog-ideas/${id}`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });

  if (response.status === 404) return undefined;
  if (!response.ok) throw new Error(`Failed to fetch idea: ${response.status}`);
  return (await response.json()) as BlogIdeaDetail;
}

async function getPublishedSlug(postId: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return undefined;

  const response = await fetch(`${backendBaseUrl}/admin/blog-posts/${postId}`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });
  if (!response.ok) return undefined;
  const post = (await response.json()) as { slug?: string };
  return post.slug;
}

async function getClaims(ideaId: string): Promise<BlogClaimItem[]> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return [];
  const response = await fetch(`${backendBaseUrl}/admin/blog-ideas/${ideaId}/claims`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });
  if (!response.ok) return [];
  return (await response.json()) as BlogClaimItem[];
}

export default async function AdminBlogIdeaDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{
    message?: string;
    opStage?: string;
    opStatus?: string;
    taskId?: string;
    blogPostId?: string;
    blogSlug?: string;
  }>;
}) {
  const id = (await params).id;
  const [query, idea] = await Promise.all([searchParams, getBlogIdea(id)]);
  if (!idea) notFound();

  const publishedSlug =
    query.blogSlug ??
    (idea.published_blog_post_id
      ? await getPublishedSlug(idea.published_blog_post_id)
      : undefined);
  const operationalStatus = {
    ...query,
    blogPostId: query.blogPostId ?? idea.published_blog_post_id ?? undefined,
    blogSlug: publishedSlug,
  };
  const claims = await getClaims(id);

  return (
    <AdminCmsShell active="ideas">
      <GenerationJobPoller
        ideaId={id}
        taskId={query.taskId}
        opStatus={query.opStatus}
      />
      <BlogIdeaDetailView
        idea={idea}
        claims={claims}
        operationalStatus={operationalStatus}
        actions={{
          approveIdea: approveOutlineAction,
          rejectIdea: rejectOutlineAction,
          generateOutline: generateOutlineAction,
          approveOutline: approveOutlineAction,
          rejectOutline: rejectOutlineAction,
          generateDraft: generateDraftAction,
          approveDraft: approveDraftAction,
          rejectDraft: rejectDraftAction,
          reviewTechnical: reviewTechnicalAction,
          approveReview: approveReviewAction,
          rejectReview: rejectReviewAction,
          generateMarketing: generateMarketingAction,
          approveMarketing: approveMarketingAction,
          rejectMarketing: rejectMarketingAction,
          publishToBlog: publishToBlogAction,
          extractClaims: extractClaimsAction,
          updateClaim: updateClaimAction,
        }}
      />
    </AdminCmsShell>
  );
}
