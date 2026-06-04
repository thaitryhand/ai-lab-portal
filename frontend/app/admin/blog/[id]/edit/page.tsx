import { headers } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { AdminBackLink } from "@/components/admin/admin-back-link";
import { AdminCmsShell } from "@/components/admin/admin-cms-shell";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { BlogEditor } from "@/components/admin/blog-editor";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { listAdminPostTags } from "@/lib/blog/tags";
import { publishAction, saveDraftAction } from "../../editor/actions";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

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

async function getAdminSession() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  return session;
}

async function getAdminBlogPost(id: string) {
  const session = await getAdminSession();

  const response = await fetch(`${backendBaseUrl}/admin/blog-posts/${id}`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });

  if (response.status === 404) return undefined;
  if (!response.ok)
    throw new Error(`Failed to fetch admin blog post: ${response.status}`);
  return (await response.json()) as AdminBlogPostDetail;
}

export default async function AdminBlogEditPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const session = await getAdminSession();
  const [post, tags] = await Promise.all([getAdminBlogPost(id), listAdminPostTags(session, id).catch(() => [])]);

  if (!post) notFound();

  return (
    <AdminCmsShell active="blog">
      <div className={adminPageStackClass}>
        <AdminPageHeader
          actions={<AdminBackLink href="/admin/blog">Back to posts</AdminBackLink>}
          description={`Editing “${post.title}”.`}
          eyebrow="Content workspace"
          metaText={`/${post.slug}`}
          status={post.status}
          title="Edit blog post"
        />

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
      </div>
    </AdminCmsShell>
  );
}
