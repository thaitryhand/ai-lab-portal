import type { Metadata } from "next";
import Link from "next/link";
import { headers } from "next/headers";
import { Plus, Rss } from "lucide-react";

import { BlogTagFilter } from "@/components/blog/blog-tag-filter";
import { PublicIndexEntry } from "@/components/public/public-index-entry";
import { PublicIndexList } from "@/components/public/public-index-list";
import { PublicPageHero } from "@/components/public/public-page-hero";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { buttonVariants } from "@/components/ui/button-variants";
import { listPublishedBlogPosts } from "@/lib/blog/posts";
import { listPublicBlogTags } from "@/lib/blog/tags";
import { auth } from "@/lib/auth/server";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { cn } from "@/lib/utils";

export const metadata = createPublicMetadata({
  title: "AI Lab Blog | AI Lab Portal",
  description:
    "Practical AI engineering notes and human-reviewed AI Lab articles.",
  path: "/blog",
  type: "website",
}) as Metadata;

export const dynamic = "force-dynamic";

export default async function BlogIndexPage({
  searchParams,
}: {
  searchParams?: Promise<{ tag?: string }>;
}) {
  const activeTag = (await searchParams)?.tag;
  const [posts, tags, session] = await Promise.all([
    listPublishedBlogPosts({ tag: activeTag }),
    listPublicBlogTags(),
    auth.api.getSession({ headers: await headers() }),
  ]);

  return (
    <PublicPageShell currentPath="/blog">
      <section className={cn(publicMainWidthClass, "flex flex-col gap-14 sm:gap-16 lg:gap-20")}>
        <PublicPageHero
          actions={
            <div className="flex items-center gap-3">
              <Link
                className={buttonVariants({ size: "icon", variant: "ghost" })}
                href="/blog/feed"
                title="RSS feed"
              >
                <Rss className="size-4 shrink-0" />
              </Link>
              {session && (
                <Link className={buttonVariants()} href="/blog/new">
                  <Plus className="size-4 shrink-0" />
                  Write a post
                </Link>
              )}
            </div>
          }
          description="Published posts from the AI Lab. Drafts and internal review material stay private."
          eyebrow="AI Lab Blog"
          title="Practical AI engineering notes."
        />

        <BlogTagFilter tags={tags} activeTag={activeTag} />

        <PublicIndexList
          emptyDescription="Published articles will appear here after an admin approves them."
          emptyTitle="No published articles yet"
          isEmpty={posts.length === 0}
        >
          {posts.map((post) => (
            <PublicIndexEntry
              key={post.slug}
              excerpt={post.excerpt}
              href={`/blog/${post.slug}`}
              imageUrl={post.imageUrl ?? undefined}
              meta={
                <>
                  {post.authorName} · {new Date(post.publishedAt).toLocaleDateString("en-US")}
                </>
              }
              title={post.title}
            />
          ))}
        </PublicIndexList>
      </section>
    </PublicPageShell>
  );
}
