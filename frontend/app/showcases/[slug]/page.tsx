import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { headers } from "next/headers";
import { notFound } from "next/navigation";
import { Pencil } from "lucide-react";

import { auth } from "@/lib/auth/server";
import { buttonVariants } from "@/components/ui/button-variants";
import { PublicArticleHeader } from "@/components/public/public-article-header";
import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { PublicProse } from "@/components/public/public-prose";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { getPublishedShowcase } from "@/lib/showcases/items";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { cn } from "@/lib/utils";

// ISR: individual showcase pages change rarely.
export const revalidate = 300;

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }): Promise<Metadata> {
  const { slug } = await params;
  const showcase = await getPublishedShowcase(slug);

  if (!showcase) {
    return createPublicMetadata({
      title: "Showcase | AI Lab Portal",
      description: "AI Lab showcase.",
      path: `/showcases/${slug}`,
    });
  }

  return createPublicMetadata({
    title: `${showcase.title} | AI Lab Portal`,
    description: showcase.heroSummary,
    ogImageUrl: showcase.imageUrl ?? undefined,
    path: `/showcases/${slug}`,
  });
}

export default async function ShowcaseDetailPage({ params }: { params: Promise<{ slug: string }> }) {
  const [{ slug }, session] = await Promise.all([
    params,
    auth.api.getSession({ headers: await headers() }),
  ]);
  const showcase = await getPublishedShowcase(slug);

  if (!showcase) {
    notFound();
  }

  return (
    <PublicPageShell currentPath="/showcases">
      <article className={cn(publicMainWidthClass, "flex flex-col gap-10 sm:gap-12")}>
        <div className="flex items-start justify-between gap-4">
          <PublicBackLink href="/showcases">Showcases</PublicBackLink>

          {session && (
            <Link
              className={cn(buttonVariants({ variant: "outline", size: "sm" }), "shrink-0")}
              href={`/admin/showcases/${showcase.id}/edit`}
            >
              <Pencil className="size-3.5 shrink-0" />
              Edit
            </Link>
          )}
        </div>

          <PublicArticleHeader
            dateLabel={new Date(showcase.publishedAt).toLocaleDateString("en-US", {
            month: "long",
            day: "numeric",
            year: "numeric",
          })}
          eyebrow={[showcase.industry, showcase.useCase].filter(Boolean).join(" · ") || "AI Lab showcase"}
          excerpt={showcase.heroSummary}
            title={showcase.title}
          />

          {showcase.imageUrl && (
            <div className="relative aspect-[16/9] w-full overflow-hidden rounded-[1.5rem] border border-border/80 bg-muted shadow-[0_24px_60px_color-mix(in_srgb,var(--primary)_7%,transparent)]">
              <Image
                alt=""
                className="object-cover"
                fill
                priority
                src={showcase.imageUrl}
                unoptimized
              />
            </div>
          )}

          <PublicProse contentMarkdown={showcase.contentMarkdown} />
      </article>
    </PublicPageShell>
  );
}
