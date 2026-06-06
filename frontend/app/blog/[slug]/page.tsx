import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { headers } from "next/headers";
import { notFound } from "next/navigation";
import { Pencil } from "lucide-react";

import { BlogComments } from "@/components/blog/blog-comments";
import { BlogSocialBar } from "@/components/blog/blog-social-bar";
import { RelatedBlogPosts } from "@/components/blog/related-blog-posts";
import { BlogShareButtons } from "@/components/blog/blog-share-buttons";
import { BlogTagChips } from "@/components/blog/blog-tag-chips";
import { PublicArticleHeader } from "@/components/public/public-article-header";
import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { PublicProse } from "@/components/public/public-prose";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { buttonVariants } from "@/components/ui/button-variants";
import { getPublishedBlogPost, listPublishedBlogPosts } from "@/lib/blog/posts";
import { getSocialStats, listComments } from "@/lib/blog/social";
import { listPublicPostTags } from "@/lib/blog/tags";
import { auth } from "@/lib/auth/server";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { blogPostingSchema, breadcrumbListSchema } from "@/lib/seo/json-ld";
import { JsonLd } from "@/components/seo/json-ld";
import { formatReadingTime } from "@/lib/reading-time";
import { cn } from "@/lib/utils";

import {
  toggleReactionAction,
  toggleBookmarkAction,
  createCommentAction,
  toggleCommentReactionAction,
  editCommentAction,
  deleteCommentAction,
} from "../actions";

export const dynamic = "force-dynamic";

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const post = await getPublishedBlogPost(slug);

  if (!post) {
    return createPublicMetadata({
      title: "Blog post | AI Lab Portal",
      description: "AI Lab blog post.",
      path: `/blog/${slug}`,
    });
  }

  return createPublicMetadata({
    title: `${post.title} | AI Lab Portal`,
    description: post.excerpt,
    ogImageUrl: post.imageUrl ?? undefined,
    ogAuthor: post.authorName,
    ogReadingTime: post.readingTime ?? undefined,
    path: `/blog/${slug}`,
    type: "article",
  });
}

export default async function BlogDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const [post, session] = await Promise.all([
    getPublishedBlogPost(slug),
    auth.api.getSession({ headers: await headers() }),
  ]);

  if (!post) {
    notFound();
  }

  const [socialStats, comments, tags, allPosts] = await Promise.all([
    session ? getSocialStats(slug, session).catch(() => null) : Promise.resolve(null),
    listComments(slug).catch(() => []),
    listPublicPostTags(slug).catch(() => []),
    listPublishedBlogPosts().catch(() => []),
  ]);
  const currentTagSlugs = new Set(tags.map((tag) => tag.slug));
  const candidatePosts = allPosts.filter((item) => item.slug !== slug);
  const candidateTags = await Promise.all(
    candidatePosts.map(async (item) => ({
      post: item,
      tags: await listPublicPostTags(item.slug).catch(() => []),
    })),
  );
  const relatedPosts = candidateTags
    .map(({ post, tags: itemTags }) => ({
      post,
      sharedTagCount: itemTags.filter((tag) => currentTagSlugs.has(tag.slug)).length,
    }))
    .sort((a, b) => {
      if (b.sharedTagCount !== a.sharedTagCount) return b.sharedTagCount - a.sharedTagCount;
      return new Date(b.post.publishedAt).getTime() - new Date(a.post.publishedAt).getTime();
    })
    .slice(0, 3)
    .map(({ post }) => post);

  return (
    <PublicPageShell currentPath="/blog">
      <JsonLd
        data={blogPostingSchema({
          headline: post.title,
          description: post.excerpt,
          url: `/blog/${slug}`,
          datePublished: post.publishedAt,
          dateModified: post.publishedAt,
          imageUrl: post.imageUrl ?? undefined,
          authorName: post.authorName,
        })}
      />
      <JsonLd
        data={breadcrumbListSchema([
          { name: "Home", url: "/" },
          { name: "Blog", url: "/blog" },
          { name: post.title, url: `/blog/${slug}` },
        ])}
      />
      <article className={cn(publicMainWidthClass, "flex flex-col gap-10 sm:gap-12")}>
        <div className="flex items-start justify-between gap-4">
          <PublicBackLink href="/blog">Blog</PublicBackLink>

          {session && (
            <Link
              className={cn(buttonVariants({ variant: "outline", size: "sm" }), "shrink-0")}
              href={`/blog/edit/${post.id}`}
            >
              <Pencil className="size-3.5 shrink-0" />
              Edit
            </Link>
          )}
        </div>

          <div className="space-y-5">
            <PublicArticleHeader
            dateLabel={new Date(post.publishedAt).toLocaleDateString("en-US", {
              month: "long",
              day: "numeric",
              year: "numeric",
            })}
            eyebrow={post.authorName}
            excerpt={post.excerpt}
            readingTimeLabel={formatReadingTime(post.readingTime)}
            title={post.title}
          />
            <BlogTagChips tags={tags} />
          </div>

          {post.imageUrl && (
            <div className="relative aspect-[16/9] w-full overflow-hidden rounded-[1.5rem] border border-border/80 bg-muted shadow-[0_24px_60px_color-mix(in_srgb,var(--primary)_7%,transparent)]">
              <Image
                alt=""
                className="object-cover"
                fill
                priority
                src={post.imageUrl}
                unoptimized
              />
            </div>
          )}

          <PublicProse contentMarkdown={post.contentMarkdown} />

        <div className="mx-auto w-full max-w-[72ch]">
          <BlogShareButtons title={post.title} slug={post.slug} />
        </div>

        <RelatedBlogPosts posts={relatedPosts} />

        {/* Social features */}
        <div className="mx-auto flex w-full max-w-[72ch] flex-col gap-8">
          <BlogSocialBar
            isAuthenticated={!!session}
            initialStats={socialStats}
            slug={slug}
            onToggleReaction={session ? toggleReactionAction : undefined}
            onToggleBookmark={session ? toggleBookmarkAction : undefined}
          />

          <BlogComments
            initialComments={comments}
            isAuthenticated={!!session}
            slug={slug}
            session={session}
            onCreateComment={session ? createCommentAction : undefined}
            onToggleCommentReaction={session ? toggleCommentReactionAction : undefined}
            onEditComment={session ? editCommentAction : undefined}
            onDeleteComment={session ? deleteCommentAction : undefined}
          />
        </div>
      </article>
    </PublicPageShell>
  );
}
