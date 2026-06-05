"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { PublicIndexEntry } from "@/components/public/public-index-entry";
import { PublicIndexList } from "@/components/public/public-index-list";
import { SkeletonCardGrid } from "@/components/public/skeleton-card";
import type { BlogPostSummary } from "@/lib/blog/posts";
import { formatReadingTime } from "@/lib/reading-time";

type Props = {
  posts: BlogPostSummary[];
  emptyTitle: string;
  emptyDescription: string;
  pageSize?: number;
};

export function InfiniteBlogList({ posts, emptyTitle, emptyDescription, pageSize = 8 }: Props) {
  const [visibleCount, setVisibleCount] = useState(pageSize);
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setVisibleCount(pageSize);
  }, [posts, pageSize]);

  const visiblePosts = useMemo(() => posts.slice(0, visibleCount), [posts, visibleCount]);
  const hasMore = visibleCount < posts.length;

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel || !hasMore) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setVisibleCount((count) => Math.min(count + pageSize, posts.length));
        }
      },
      { rootMargin: "480px 0px" },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, pageSize, posts.length]);

  return (
    <div className="flex flex-col gap-6">
      <PublicIndexList
        emptyDescription={emptyDescription}
        emptyTitle={emptyTitle}
        isEmpty={posts.length === 0}
      >
        {visiblePosts.map((post) => (
          <PublicIndexEntry
            key={post.slug}
            excerpt={post.excerpt}
            href={`/blog/${post.slug}`}
            imageUrl={post.imageUrl ?? undefined}
            readingTimeLabel={formatReadingTime(post.readingTime)}
            meta={
              <>
                {post.authorName} · {new Date(post.publishedAt).toLocaleDateString("en-US")}
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
          <SkeletonCardGrid count={2} />
        </div>
      ) : posts.length > pageSize ? (
        <p className="text-center text-sm text-muted-foreground">You&apos;re all caught up.</p>
      ) : null}
    </div>
  );
}
