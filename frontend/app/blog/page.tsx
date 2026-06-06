import type { Metadata } from "next";
import Link from "next/link";
import { headers } from "next/headers";
import { Plus, Rss } from "lucide-react";
import { Suspense } from "react";

import { BlogTagFilter } from "@/components/blog/blog-tag-filter";
import { InfiniteBlogList } from "@/components/blog/infinite-blog-list";
import { PublicPageHero } from "@/components/public/public-page-hero";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { SearchInput } from "@/components/public/search-input";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { buttonVariants } from "@/components/ui/button-variants";
import { listPublishedBlogPostsPage, type BlogFeed } from "@/lib/blog/posts";
import { listPublicBlogTags } from "@/lib/blog/tags";
import { auth } from "@/lib/auth/server";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { breadcrumbListSchema, itemListSchema } from "@/lib/seo/json-ld";
import { JsonLd } from "@/components/seo/json-ld";
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
  searchParams?: Promise<{ tag?: string; feed?: string; q?: string }>;
}) {
  const resolvedSearchParams = await searchParams;
  const activeTag = resolvedSearchParams?.tag;
  const activeFeed: BlogFeed = resolvedSearchParams?.feed === "following" || resolvedSearchParams?.feed === "discover" ? resolvedSearchParams.feed : "latest";
  const searchQuery = resolvedSearchParams?.q;
  const session = await auth.api.getSession({ headers: await headers() });
  const [postsPage, tags] = await Promise.all([
    activeFeed === "following" && !session ? Promise.resolve({ items: [], page: 1, limit: 8, total: 0, hasMore: false }) : listPublishedBlogPostsPage({ tag: activeTag, feed: activeFeed, session, q: searchQuery, page: 1, limit: 8 }),
    listPublicBlogTags(),
  ]);
  const posts = postsPage.items;

  return (
    <PublicPageShell currentPath="/blog">
      <JsonLd
        data={breadcrumbListSchema([
          { name: "Home", url: "/" },
          { name: "Blog", url: "/blog" },
        ])}
      />
      {posts.length > 0 && (
        <JsonLd
          data={itemListSchema({
            items: posts,
            itemUrl: (p) => `/blog/${p.slug}`,
            itemName: (p) => p.title,
            numberOfItems: postsPage.total,
          })}
        />
      )}
      <section className={cn(publicMainWidthClass, "flex flex-col gap-14 sm:gap-16 lg:gap-20")}>
        <PublicPageHero
          actions={
            <div className="flex items-center gap-3">
              <Link
                className={buttonVariants({ size: "icon", variant: "ghost" })}
                href="/feed.xml"
                title="RSS feed"
              >
                <Rss className="size-4 shrink-0" />
              </Link>
              <Link
                className={buttonVariants()}
                href={session ? "/blog/new" : "/login"}
              >
                <Plus className="size-4 shrink-0" />
                Write a post
              </Link>
            </div>
          }
          description="Published posts from the AI Lab. Drafts and internal review material stay private."
          eyebrow="AI Lab Blog"
          title="Practical AI engineering notes."
        />

        <div className="-mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <Suspense fallback={<div className="h-10 w-full max-w-md" />}>
            <SearchInput placeholder="Search blog posts…" />
          </Suspense>
        </div>

        <div className="flex flex-wrap gap-2">
          {(["latest", "following", "discover"] as const).map((feed) => {
            const href = new URLSearchParams();
            if (feed !== "latest") href.set("feed", feed);
            if (activeTag) href.set("tag", activeTag);
            const label = feed[0].toUpperCase() + feed.slice(1);
            return (
              <Link
                key={feed}
                href={`/blog${href.toString() ? `?${href.toString()}` : ""}`}
                className={cn(
                  "rounded-full border px-4 py-2 text-sm font-medium transition",
                  activeFeed === feed ? "border-brand bg-brand text-brand-foreground" : "text-muted-foreground hover:border-brand/40 hover:text-foreground",
                )}
              >
                {label}
              </Link>
            );
          })}
        </div>

        {activeFeed === "following" && !session && (
          <div className="rounded-2xl border border-dashed border-border bg-card/50 px-6 py-10 text-center">
            <p className="text-sm text-muted-foreground">
              <Link href="/login" className="font-medium text-brand underline underline-offset-2 hover:text-brand/80">
                Sign in
              </Link>{" "}
              to follow authors and build a personalized feed.
            </p>
          </div>
        )}

        <BlogTagFilter tags={tags} activeTag={activeTag} />

        <InfiniteBlogList
          initialPosts={posts}
          initialHasMore={postsPage.hasMore}
          tag={activeTag}
          feed={activeFeed}
          query={searchQuery}
          emptyDescription={activeFeed === "following" && !session ? "" : activeFeed === "following" ? "Follow authors to populate this feed." : "Published articles will appear here after an admin approves them."}
          emptyTitle={activeFeed === "following" ? "No following feed yet" : "No published articles yet"}
        />
      </section>
    </PublicPageShell>
  );
}
