import type { Metadata } from "next";
import Link from "next/link";

import { PublicLabSection } from "@/components/public/public-lab-section";
import { PublicPageHero } from "@/components/public/public-page-hero";
import { PublicPageShell } from "@/components/public/public-page-shell";
import {
  publicMainWidthClass,
  publicPrimaryCtaClass,
  publicSecondaryCtaClass,
} from "@/components/public/public-ui";
import { listPublishedBlogPosts } from "@/lib/blog/posts";
import { listPublishedShowcases } from "@/lib/showcases/items";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { cn } from "@/lib/utils";

export const metadata: Metadata = createPublicMetadata({
  title: "AI Lab | AI Lab Portal",
  description: "Human-reviewed AI engineering, showcases, and practical publishing workflows.",
  path: "/lab",
});

// ISR: lab page aggregates published content; revalidate every 10 minutes.
export const revalidate = 600;

export default async function LabPage() {
  const [showcases, posts] = await Promise.all([listPublishedShowcases(), listPublishedBlogPosts()]);

  return (
    <PublicPageShell currentPath="/lab">
      <div className={cn(publicMainWidthClass, "flex flex-col gap-20 sm:gap-24 lg:gap-28")}>
        <PublicPageHero
          actions={
            <>
              <Link className={publicPrimaryCtaClass} href="/showcases">
                View showcases
              </Link>
              <Link className={publicSecondaryCtaClass} href="/blog">
                Read the blog
              </Link>
            </>
          }
            description="The AI Lab portal combines manual publishing, client-ready showcases, and practical engineering notes. AI assists drafting; humans approve what goes live."
            eyebrow="AI Lab"
            title="Human-reviewed AI engineering."
            variant="panel"
          />

        {showcases.length > 0 ? (
          <PublicLabSection
            index="01"
            items={showcases.slice(0, 3).map((showcase) => ({
              excerpt: showcase.heroSummary,
              href: `/showcases/${showcase.slug}`,
              meta: (
                <>
                  {showcase.industry ?? "AI Lab"} · {showcase.useCase ?? "Delivery"}
                </>
              ),
              title: showcase.title,
            }))}
            moreHref="/showcases"
            moreLabel="All showcases"
            sectionIndex={0}
            title="Featured showcases"
          />
        ) : null}

        {posts.length > 0 ? (
          <PublicLabSection
            index="02"
            items={posts.slice(0, 3).map((post) => ({
              excerpt: post.excerpt,
              href: `/blog/${post.slug}`,
              meta: post.authorName,
              title: post.title,
            }))}
            moreHref="/blog"
            moreLabel="All articles"
            sectionIndex={1}
            title="Latest articles"
          />
        ) : null}
      </div>
    </PublicPageShell>
  );
}
