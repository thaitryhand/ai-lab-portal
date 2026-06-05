import type { Metadata } from "next";
import Link from "next/link";
import { Hash } from "lucide-react";

import { PublicPageHero } from "@/components/public/public-page-hero";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { listPublicBlogTags } from "@/lib/blog/tags";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { cn } from "@/lib/utils";

export const metadata: Metadata = createPublicMetadata({
  title: "Blog Tags | AI Lab Portal",
  description: "Browse AI Lab blog posts by topic.",
  path: "/blog/tags",
});

export const dynamic = "force-dynamic";

export default async function BlogTagsPage() {
  const tags = await listPublicBlogTags().catch(() => []);

  return (
    <PublicPageShell currentPath="/blog">
      <section className={cn(publicMainWidthClass, "flex flex-col gap-12 sm:gap-14")}> 
        <PublicPageHero
          eyebrow="Topics"
          title="Browse blog tags."
          description="Explore AI Lab articles by workflow, tooling, and engineering topic."
        />

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {tags.map((tag) => (
            <Link
              key={tag.id}
              href={`/blog/tags/${encodeURIComponent(tag.slug)}`}
              className="group rounded-2xl border border-border/80 bg-card/80 p-5 transition-colors hover:border-brand/35 hover:bg-muted/25"
            >
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Hash className="size-4 text-brand" />
                {tag.postCount} post{tag.postCount === 1 ? "" : "s"}
              </div>
              <h2 className="mt-3 text-xl font-semibold tracking-[-0.02em] text-foreground group-hover:text-brand">
                {tag.name}
              </h2>
            </Link>
          ))}
        </div>
      </section>
    </PublicPageShell>
  );
}
