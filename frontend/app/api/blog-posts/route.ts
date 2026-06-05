import { NextResponse } from "next/server";
import { headers } from "next/headers";

import { auth } from "@/lib/auth/server";
import { listPublishedBlogPostsPage, type BlogFeed } from "@/lib/blog/posts";

function normalizeFeed(feed: string | null): BlogFeed {
  return feed === "following" || feed === "discover" ? feed : "latest";
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const page = Number(url.searchParams.get("page") ?? "1");
  const limit = Number(url.searchParams.get("limit") ?? "8");
  const tag = url.searchParams.get("tag") ?? undefined;
  const q = url.searchParams.get("q") ?? undefined;
  const feed = normalizeFeed(url.searchParams.get("feed"));
  const session = await auth.api.getSession({ headers: await headers() });

  if (feed === "following" && !session) {
    return NextResponse.json({ items: [], page, limit, total: 0, hasMore: false });
  }

  try {
    const posts = await listPublishedBlogPostsPage({
      tag,
      q,
      feed,
      page: Number.isFinite(page) && page > 0 ? page : 1,
      limit: Number.isFinite(limit) && limit > 0 ? limit : 8,
      session,
    });
    return NextResponse.json(posts);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Failed to fetch blog posts" },
      { status: 500 },
    );
  }
}
