import { estimateReadingTime } from "@/lib/reading-time";
import { createUserBoundaryHeaders } from "@/lib/admin/fastapi-boundary";

type Session = { user: { id: string; email: string } };

export type BlogFeed = "latest" | "following" | "discover";

export type BlogPostSummary = {
  slug: string;
  title: string;
  excerpt: string;
  authorName: string;
  publishedAt: string;
  imageUrl?: string | null;
  authorUserId?: string | null;
  readingTime: number;
};

export type BlogPostDetail = BlogPostSummary & {
  id: string;
  contentMarkdown: string;
};

export type PaginatedBlogPosts = {
  items: BlogPostSummary[];
  page: number;
  limit: number;
  total: number;
  hasMore: boolean;
};

type ApiBlogPostSummary = {
  slug: string;
  title: string;
  excerpt: string;
  author_name: string;
  published_at: string;
  image_url?: string | null;
  author_user_id?: string | null;
};

type ApiBlogPostDetail = ApiBlogPostSummary & {
  id: string;
  content_markdown: string;
};

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

function toSummary(post: ApiBlogPostSummary): BlogPostSummary {
  return {
    slug: post.slug,
    title: post.title,
    excerpt: post.excerpt,
    authorName: post.author_name,
    publishedAt: post.published_at,
    imageUrl: post.image_url,
    authorUserId: post.author_user_id,
    readingTime: estimateReadingTime(post.excerpt),
  };
}

function toDetail(post: ApiBlogPostDetail): BlogPostDetail {
  return {
    ...toSummary(post),
    id: post.id,
    contentMarkdown: post.content_markdown,
    readingTime: estimateReadingTime(post.content_markdown),
  };
}

export async function listPublishedBlogPosts(options?: { tag?: string; feed?: BlogFeed; session?: Session | null; q?: string }): Promise<BlogPostSummary[]> {
  const url = new URL(`${backendBaseUrl}/public/blog-posts`);
  if (options?.tag) url.searchParams.set("tag", options.tag);
  if (options?.feed) url.searchParams.set("feed", options.feed);
  if (options?.q) url.searchParams.set("q", options.q);
  const response = await fetch(url.toString(), {
    headers: options?.session ? createUserBoundaryHeaders(options.session) : undefined,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch published blog posts: ${response.status}`);
  }

  const posts = (await response.json()) as ApiBlogPostSummary[];
  return posts.map(toSummary);
}

export async function listPublishedBlogPostsPage(options?: { tag?: string; feed?: BlogFeed; session?: Session | null; q?: string; page?: number; limit?: number }): Promise<PaginatedBlogPosts> {
  const url = new URL(`${backendBaseUrl}/public/blog-posts`);
  if (options?.tag) url.searchParams.set("tag", options.tag);
  if (options?.feed) url.searchParams.set("feed", options.feed);
  if (options?.q) url.searchParams.set("q", options.q);
  url.searchParams.set("paginated", "true");
  url.searchParams.set("page", String(options?.page ?? 1));
  url.searchParams.set("limit", String(options?.limit ?? 8));

  const response = await fetch(url.toString(), {
    headers: options?.session ? createUserBoundaryHeaders(options.session) : undefined,
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch paginated blog posts: ${response.status}`);
  }

  const data = (await response.json()) as {
    items: ApiBlogPostSummary[];
    page: number;
    limit: number;
    total: number;
    has_more: boolean;
  };

  return {
    items: data.items.map(toSummary),
    page: data.page,
    limit: data.limit,
    total: data.total,
    hasMore: data.has_more,
  };
}

export async function getPublishedBlogPost(slug: string): Promise<BlogPostDetail | undefined> {
  const response = await fetch(`${backendBaseUrl}/public/blog-posts/${slug}`);

  if (response.status === 404) {
    return undefined;
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch published blog post: ${response.status}`);
  }

  return toDetail((await response.json()) as ApiBlogPostDetail);
}
