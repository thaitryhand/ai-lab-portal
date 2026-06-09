import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type Session = { user: { id: string; email: string } };

export type BlogTag = {
  id: string;
  slug: string;
  name: string;
  postCount: number;
};

type ApiBlogTag = {
  id: string;
  slug: string;
  name: string;
  post_count: number;
};

function toTag(tag: ApiBlogTag): BlogTag {
  return { id: tag.id, slug: tag.slug, name: tag.name, postCount: tag.post_count };
}

export async function listPublicBlogTags(): Promise<BlogTag[]> {
  const response = await fetch(`${backendBaseUrl}/public/blog-tags`);
  if (!response.ok) throw new Error(`Failed to fetch blog tags: ${response.status}`);
  return ((await response.json()) as ApiBlogTag[]).map(toTag);
}

export async function listPublicPostTags(slug: string): Promise<BlogTag[]> {
  const response = await fetch(`${backendBaseUrl}/public/blog-posts/${slug}/tags`);
  if (response.status === 404) return [];
  if (!response.ok) throw new Error(`Failed to fetch post tags: ${response.status}`);
  return ((await response.json()) as ApiBlogTag[]).map(toTag);
}

async function callAdmin<T>(session: Session, path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${backendBaseUrl}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...createAdminBoundaryHeaders(session),
      ...init?.headers,
    },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Admin tag API failed: ${response.status}`);
  return response.json() as Promise<T>;
}

export async function listAdminBlogTags(session: Session): Promise<BlogTag[]> {
  return (await callAdmin<ApiBlogTag[]>(session, "/admin/blog-tags")).map(toTag);
}

export async function createAdminBlogTag(session: Session, name: string): Promise<BlogTag> {
  return toTag(await callAdmin<ApiBlogTag>(session, "/admin/blog-tags", { method: "POST", body: JSON.stringify({ name }) }));
}

export async function listAdminPostTags(session: Session, postId: string): Promise<BlogTag[]> {
  return (await callAdmin<ApiBlogTag[]>(session, `/admin/blog-posts/${postId}/tags`)).map(toTag);
}

export async function setAdminPostTags(session: Session, postId: string, tagIds: string[]): Promise<BlogTag[]> {
  return (await callAdmin<ApiBlogTag[]>(session, `/admin/blog-posts/${postId}/tags`, {
    method: "PUT",
    body: JSON.stringify({ tag_ids: tagIds }),
  })).map(toTag);
}
