import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import type { BlogPostSummary } from "@/lib/blog/posts";
import { formatReadingTime } from "@/lib/reading-time";

export function RelatedBlogPosts({ posts }: { posts: BlogPostSummary[] }) {
  if (posts.length === 0) return null;

  return (
    <section className="border-t border-border/80 pt-10 sm:pt-12">
      <div className="mb-5 flex items-center justify-between gap-4">
        <div>
          <h2 className="font-(family-name:--font-gt-super) text-3xl font-normal tracking-[-0.03em] text-foreground">
            Related reading
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">More AI Lab notes worth opening next.</p>
        </div>
        <Link href="/blog" className="hidden text-sm font-semibold text-brand hover:underline sm:inline">
          View all
        </Link>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {posts.map((post) => (
          <Link
            key={post.slug}
            href={`/blog/${post.slug}`}
            className="group rounded-2xl border border-border/80 bg-card/80 p-5 transition-colors hover:border-brand/35 hover:bg-muted/25"
          >
            <div className="flex items-start justify-between gap-3">
              <p className="text-xs font-medium text-muted-foreground">
                {formatReadingTime(post.readingTime)}
              </p>
              <ArrowUpRight className="size-4 shrink-0 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-brand" />
            </div>
            <h3 className="mt-3 line-clamp-2 text-base font-semibold leading-snug text-foreground group-hover:text-brand">
              {post.title}
            </h3>
            <p className="mt-2 line-clamp-3 text-sm leading-6 text-muted-foreground">{post.excerpt}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
