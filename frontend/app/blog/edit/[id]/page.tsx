import { headers } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { BlogEditor } from "@/components/admin/blog-editor";
import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { publishAction, saveDraftAction } from "@/app/admin/blog/editor/actions";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { listAdminPostTags } from "@/lib/blog/tags";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export const metadata = {
  title: "Edit blog post | AI Lab Portal",
  description: "Edit an existing blog post.",
};

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type AdminBlogPostDetail = {
  id: string;
  slug: string;
  title: string;
  status: "draft" | "published";
  published_at: string | null;
  excerpt: string;
  author_name: string;
  content_markdown: string;
  image_url?: string | null;
};

async function getAdminBlogPost(id: string) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) return undefined;

  const response = await fetch(`${backendBaseUrl}/admin/blog-posts/${id}`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });

  if (response.status === 404) return undefined;
  if (!response.ok) throw new Error(`Failed to fetch admin blog post: ${response.status}`);
  return (await response.json()) as AdminBlogPostDetail;
}

export default async function BlogEditPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const [{ id }, session] = await Promise.all([
    params,
    auth.api.getSession({ headers: await headers() }),
  ]);

  if (!session) {
    redirect("/admin/login?redirect=/blog/edit/" + id);
  }

  const [post, tags] = await Promise.all([getAdminBlogPost(id), listAdminPostTags(session, id).catch(() => [])]);
  if (!post) notFound();

  return (
    <PublicPageShell>
      <section className={cn(publicMainWidthClass, "flex flex-col gap-8 py-10 sm:py-14")}>
        <PublicBackLink href="/blog">Blog</PublicBackLink>

        <BlogEditor
          initialAuthorName={post.author_name}
          initialContentMarkdown={post.content_markdown}
          initialExcerpt={post.excerpt}
          initialImageUrl={post.image_url ?? undefined}
          initialPostId={post.id}
          initialTagNames={tags.map((tag) => tag.name)}
          initialSlug={post.slug}
          initialTitle={post.title}
          publishAction={publishAction}
          saveDraftAction={saveDraftAction}
        />
      </section>
    </PublicPageShell>
  );
}
