import Link from "next/link";

import type { BlogTag } from "@/lib/blog/tags";
import { cn } from "@/lib/utils";

type Props = {
  tags: BlogTag[];
  activeTag?: string;
};

export function BlogTagFilter({ tags, activeTag }: Props) {
  if (tags.length === 0) return null;
  return (
    <nav aria-label="Filter blog posts by tag" className="flex flex-wrap gap-2">
      <Link
        href="/blog"
        className={cn(
          "rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
          !activeTag ? "border-brand/40 bg-brand/10 text-brand" : "border-border text-muted-foreground hover:text-foreground",
        )}
      >
        All
      </Link>
      {tags.map((tag) => (
        <Link
          key={tag.id}
          href={`/blog?tag=${encodeURIComponent(tag.slug)}`}
          className={cn(
            "rounded-full border px-3 py-1.5 text-sm font-medium transition-colors",
            activeTag === tag.slug
              ? "border-brand/40 bg-brand/10 text-brand"
              : "border-border text-muted-foreground hover:text-foreground",
          )}
        >
          {tag.name}
          {tag.postCount > 0 && <span className="ml-1 text-xs tabular-nums opacity-70">{tag.postCount}</span>}
        </Link>
      ))}
    </nav>
  );
}
