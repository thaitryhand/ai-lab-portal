import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { headers } from "next/headers";
import { notFound } from "next/navigation";
import { Pencil } from "lucide-react";

import { PublicArticleHeader } from "@/components/public/public-article-header";
import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { PublicProse } from "@/components/public/public-prose";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { buttonVariants } from "@/components/ui/button-variants";
import { getPublishedBlogPost } from "@/lib/blog/posts";
import { auth } from "@/lib/auth/server";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { cn } from "@/lib/utils";

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

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: post.title,
    description: post.excerpt,
    image: post.imageUrl,
    author: {
      "@type": "Person",
      name: post.authorName,
    },
    datePublished: post.publishedAt,
  };

  return (
    <PublicPageShell currentPath="/blog">
      <script
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        type="application/ld+json"
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

        {post.imageUrl && (
          <div className="relative aspect-[2/1] w-full overflow-hidden rounded-xl border">
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

        <PublicArticleHeader
          dateLabel={new Date(post.publishedAt).toLocaleDateString("en-US", {
            month: "long",
            day: "numeric",
            year: "numeric",
          })}
          eyebrow={post.authorName}
          excerpt={post.excerpt}
          title={post.title}
        />

        <PublicProse contentMarkdown={post.contentMarkdown} />
      </article>
    </PublicPageShell>
  );
}
