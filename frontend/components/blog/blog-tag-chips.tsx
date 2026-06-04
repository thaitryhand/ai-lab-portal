import Link from "next/link";

import type { BlogTag } from "@/lib/blog/tags";
import { cn } from "@/lib/utils";

type Props = {
  tags: BlogTag[];
  className?: string;
};

export function BlogTagChips({ tags, className }: Props) {
  if (tags.length === 0) return null;
  return (
    <div className={cn("flex flex-wrap gap-2", className)}>
      {tags.map((tag) => (
        <Link
          key={tag.id}
          href={`/blog?tag=${encodeURIComponent(tag.slug)}`}
          className="rounded-full border border-border bg-card px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:border-brand/40 hover:text-brand"
        >
          #{tag.name}
        </Link>
      ))}
    </div>
  );
}
