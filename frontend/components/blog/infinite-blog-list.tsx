"use client";

import { useEffect, useRef, useState, useTransition } from "react";

import { PublicIndexEntry } from "@/components/public/public-index-entry";
import { PublicIndexList } from "@/components/public/public-index-list";
import { SkeletonCardGrid } from "@/components/public/skeleton-card";
import type { BlogFeed, BlogPostSummary } from "@/lib/blog/posts";
import { formatReadingTime } from "@/lib/reading-time";

type Props = {
  initialPosts: BlogPostSummary[];
  initialHasMore: boolean;
  emptyTitle: string;
  emptyDescription: string;
  pageSize?: number;
  tag?: string;
  feed?: BlogFeed;
  query?: string;
};

type ApiPage = {
  items: BlogPostSummary[];
  page: number;
  limit: number;
  total: number;
  hasMore: boolean;
};

type ListState = {
  hasMore: boolean;
  page: number;
  posts: BlogPostSummary[];
  resetKey: string;
};

function buildUrl({
  page,
  pageSize,
  tag,
  feed,
  query,
}: {
  page: number;
  pageSize: number;
  tag?: string;
  feed?: BlogFeed;
  query?: string;
}) {
  const params = new URLSearchParams({
    page: String(page),
    limit: String(pageSize),
  });
  if (tag) params.set("tag", tag);
  if (feed && feed !== "latest") params.set("feed", feed);
  if (query) params.set("q", query);
  return `/api/blog-posts?${params.toString()}`;
}

export function InfiniteBlogList({
  initialPosts,
  initialHasMore,
  emptyTitle,
  emptyDescription,
  pageSize = 8,
  tag,
  feed = "latest",
  query,
}: Props) {
  // Stable reset key derived only from filter params (not post data)
  const filterKey = `${feed}:${tag ?? ""}:${query ?? ""}`;
  const [listState, setListState] = useState<ListState>({
    hasMore: initialHasMore,
    page: 1,
    posts: initialPosts,
    resetKey: filterKey,
  });
  const [isPending, startTransition] = useTransition();
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const inFlightRef = useRef(false);
  const prevFilterKeyRef = useRef(filterKey);

  // Reset when filters change, only once per filter change
  useEffect(() => {
    if (filterKey !== prevFilterKeyRef.current) {
      prevFilterKeyRef.current = filterKey;
      setListState({
        hasMore: initialHasMore,
        page: 1,
        posts: initialPosts,
        resetKey: filterKey,
      });
    }
  }, [filterKey, initialHasMore, initialPosts]);

  const { hasMore, page, posts } = listState;

  useEffect(() => {
    inFlightRef.current = false;
  }, [filterKey]);

  useEffect(() => {
    if (!hasMore) return;
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry?.isIntersecting || inFlightRef.current) return;
        inFlightRef.current = true;
        const nextPage = page + 1;
        startTransition(async () => {
          try {
            const response = await fetch(
              buildUrl({ page: nextPage, pageSize, tag, feed, query }),
            );
            if (!response.ok) throw new Error("Failed to load more posts");
            const data = (await response.json()) as ApiPage;
            setListState((current) => {
              const seen = new Set(current.posts.map((post) => post.slug));
              return {
                ...current,
                hasMore: data.hasMore,
                page: data.page,
                posts: [
                  ...current.posts,
                  ...data.items.filter((post) => !seen.has(post.slug)),
                ],
              };
            });
          } finally {
            inFlightRef.current = false;
          }
        });
      },
      { rootMargin: "480px 0px" },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [feed, hasMore, page, pageSize, query, tag]);

  return (
    <div className="flex flex-col gap-6">
      <PublicIndexList
        emptyDescription={emptyDescription}
        emptyTitle={emptyTitle}
        isEmpty={posts.length === 0}
      >
        {posts.map((post) => (
          <PublicIndexEntry
            key={post.slug}
            excerpt={post.excerpt}
            href={`/blog/${post.slug}`}
            imageUrl={post.imageUrl ?? undefined}
            readingTimeLabel={formatReadingTime(post.readingTime)}
            meta={
              <>
                {post.authorName} ·{" "}
                {new Date(post.publishedAt).toLocaleDateString("en-US")}
              </>
            }
            showBookmark
            slug={post.slug}
            title={post.title}
          />
        ))}
      </PublicIndexList>

      {hasMore ? (
        <div ref={sentinelRef} className="pt-2" aria-label="Loading more posts">
          <SkeletonCardGrid count={isPending ? 2 : 1} />
        </div>
      ) : posts.length > pageSize ? (
        <p className="text-center text-sm text-muted-foreground">
          You&apos;re all caught up.
        </p>
      ) : null}
    </div>
  );
}
