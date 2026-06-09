"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Clock } from "lucide-react";

type RelatedPost = {
  slug: string;
  title: string;
  excerpt: string;
  published_at: string | null;
  image_url: string | null;
  reading_time_minutes: number;
};

export function RelatedPosts({ slug }: { slug: string }) {
  const [posts, setPosts] = useState<RelatedPost[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`/api/blog/${slug}/related`, {
      signal: controller.signal,
    })
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => {
        setPosts(data || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
    return () => controller.abort();
  }, [slug]);

  if (loading || posts.length === 0) return null;

  return (
    <section className="mt-16 border-t pt-10">
      <h2 className="mb-6 text-xl font-semibold tracking-tight">Related Articles</h2>
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {posts.map((post) => (
          <Link
            key={post.slug}
            href={`/blog/${post.slug}`}
            className="group rounded-lg border bg-card p-5 text-card-foreground shadow-sm transition-all hover:border-brand/30 hover:shadow-md"
          >
            <h3 className="mb-2 text-sm font-semibold leading-snug group-hover:text-brand">
              {post.title}
            </h3>
            <p className="mb-3 line-clamp-2 text-xs leading-relaxed text-muted-foreground">
              {post.excerpt}
            </p>
            <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
              {post.reading_time_minutes > 0 && (
                <span className="inline-flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {post.reading_time_minutes} min read
                </span>
              )}
              {post.published_at && (
                <time dateTime={post.published_at}>
                  {new Date(post.published_at).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </time>
              )}
            </div>
            <div className="mt-3 flex items-center gap-1 text-xs font-medium text-brand opacity-0 transition-opacity group-hover:opacity-100">
              Read more <ArrowRight className="h-3 w-3" />
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
