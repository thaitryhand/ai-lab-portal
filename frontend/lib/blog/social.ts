import { createUserBoundaryHeaders } from "@/lib/admin/fastapi-boundary";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type SessionUser = { id: string; email: string };
type BetterAuthSession = { user: SessionUser };

// ─── Types ───────────────────────────────────────────────────────────────────

export type ReactionCounts = Record<string, number>;

export type SocialStats = {
  post_id: string;
  reaction_counts: ReactionCounts;
  user_reactions: string[];
  is_bookmarked: boolean;
  comment_count: number;
};

export type BlogCommentPublic = {
  id: string;
  user_id: string;
  user_name: string | null;
  avatar_url: string | null;
  content: string;
  parent_id: string | null;
  created_at: string;
  reaction_count?: number;
  user_reacted?: boolean;
};

export type BlogBookmark = {
  id: string;
  post_id: string;
  slug: string;
  title: string;
  user_id: string;
  created_at: string;
};

export type AdminCommentSummary = {
  id: string;
  post_id: string;
  post_title: string;
  user_id: string;
  user_email: string | null;
  user_name: string | null;
  content: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
};

// ─── API client ──────────────────────────────────────────────────────────────

async function callApi<T>(path: string, session: BetterAuthSession, init?: RequestInit): Promise<T> {
  const headers = {
    "content-type": "application/json",
    ...createUserBoundaryHeaders(session),
    ...init?.headers,
  };

  const response = await fetch(`${backendBaseUrl}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`API call failed: ${response.status} ${text}`);
  }

  return response.json();
}

// ─── Social stats ────────────────────────────────────────────────────────────

export async function getSocialStats(slug: string, session: BetterAuthSession): Promise<SocialStats | null> {
  try {
    return await callApi<SocialStats>(`/public/blog-posts/${slug}/social-stats`, session);
  } catch {
    return null;
  }
}

export async function toggleReaction(slug: string, emoji: string, session: BetterAuthSession): Promise<SocialStats> {
  return await callApi<SocialStats>(`/public/blog-posts/${slug}/reactions`, session, {
    method: "POST",
    body: JSON.stringify({ emoji }),
  });
}

export async function toggleBookmark(slug: string, session: BetterAuthSession): Promise<SocialStats> {
  return await callApi<SocialStats>(`/public/blog-posts/${slug}/bookmarks`, session, {
    method: "POST",
  });
}

// ─── Comments ────────────────────────────────────────────────────────────────

export async function listComments(slug: string): Promise<BlogCommentPublic[]> {
  try {
    const response = await fetch(`${backendBaseUrl}/public/blog-posts/${slug}/comments`, { cache: "no-store" });
    if (!response.ok) return [];
    return (await response.json()) as BlogCommentPublic[];
  } catch {
    return [];
  }
}

export async function createComment(
  slug: string,
  content: string,
  parentId: string | undefined,
  session: BetterAuthSession,
): Promise<BlogCommentPublic> {
  const body: Record<string, string> = { content };
  if (parentId) body.parent_id = parentId;
  return await callApi<BlogCommentPublic>(`/public/blog-posts/${slug}/comments`, session, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

// ─── Bookmarks (user) ────────────────────────────────────────────────────────

export async function listUserBookmarks(session: BetterAuthSession): Promise<BlogBookmark[]> {
  try {
    return await callApi<BlogBookmark[]>("/user/bookmarks", session);
  } catch {
    return [];
  }
}

export async function checkBookmark(slug: string, session: BetterAuthSession): Promise<boolean> {
  try {
    return await callApi<boolean>(`/user/bookmarks/check/${slug}`, session);
  } catch {
    return false;
  }
}

// ─── Comment reactions ───────────────────────────────────────────────────

export type CommentReactionResponse = {
  reacted: boolean;
  count: number;
};

export async function toggleCommentReaction(
  slug: string,
  commentId: string,
  session: BetterAuthSession,
): Promise<CommentReactionResponse> {
  return await callApi<CommentReactionResponse>(
    `/public/blog-posts/${slug}/comments/${commentId}/react`,
    session,
    { method: "POST" },
  );
}

// ─── Comment edit/delete ─────────────────────────────────────────────────

export async function editComment(
  slug: string,
  commentId: string,
  content: string,
  session: BetterAuthSession,
): Promise<BlogCommentPublic> {
  return await callApi<BlogCommentPublic>(
    `/public/blog-posts/${slug}/comments/${commentId}`,
    session,
    {
      method: "PATCH",
      body: JSON.stringify({ content }),
    },
  );
}

export async function deleteComment(
  slug: string,
  commentId: string,
  session: BetterAuthSession,
): Promise<{ deleted: boolean }> {
  return await callApi<{ deleted: boolean }>(
    `/public/blog-posts/${slug}/comments/${commentId}`,
    session,
    { method: "DELETE" },
  );
}
