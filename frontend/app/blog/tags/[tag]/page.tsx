import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

import { InfiniteBlogList } from "@/components/blog/infinite-blog-list";
import { PublicPageHero } from "@/components/public/public-page-hero";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { listPublishedBlogPostsPage } from "@/lib/blog/posts";
import { listPublicBlogTags } from "@/lib/blog/tags";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { breadcrumbListSchema, itemListSchema } from "@/lib/seo/json-ld";
import { JsonLd } from "@/components/seo/json-ld";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<{ tag: string }> }): Promise<Metadata> {
  const { tag } = await params;
  const tags = await listPublicBlogTags().catch(() => []);
  const found = tags.find((item) => item.slug === tag);
  const name = found?.name ?? tag;
  return createPublicMetadata({
    title: `${name} Articles | AI Lab Portal`,
    description: `AI Lab blog posts tagged ${name}.`,
    path: `/blog/tags/${tag}`,
  });
}

export default async function BlogTagPage({ params }: { params: Promise<{ tag: string }> }) {
  const { tag } = await params;
  const [tags, postsPage] = await Promise.all([
    listPublicBlogTags().catch(() => []),
    listPublishedBlogPostsPage({ tag, page: 1, limit: 8 }).catch(() => ({ items: [], page: 1, limit: 8, total: 0, hasMore: false })),
  ]);
  const posts = postsPage.items;
  const found = tags.find((item) => item.slug === tag);
  const name = found?.name ?? tag;

  return (
    <PublicPageShell currentPath="/blog">
      <JsonLd
        data={breadcrumbListSchema([
          { name: "Home", url: "/" },
          { name: "Blog", url: "/blog" },
          { name: "Tags", url: "/blog/tags" },
          { name: `#${name}`, url: `/blog/tags/${tag}` },
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
      <section className={cn(publicMainWidthClass, "flex flex-col gap-12 sm:gap-14")}> 
        <Link href="/blog/tags" className="inline-flex w-fit items-center gap-1.5 text-sm font-semibold text-muted-foreground hover:text-brand">
          <ArrowLeft className="size-4" />
          All tags
        </Link>
        <PublicPageHero
          eyebrow="Topic"
          title={`#${name}`}
          description={`${posts.length} article${posts.length === 1 ? "" : "s"} filed under ${name}.`}
        />
        <InfiniteBlogList
          initialPosts={posts}
          initialHasMore={postsPage.hasMore}
          tag={tag}
          emptyTitle="No articles for this tag yet"
          emptyDescription="Articles will appear here after they are tagged and published."
        />
      </section>
    </PublicPageShell>
  );
}
