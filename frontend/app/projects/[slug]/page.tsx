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
import { getPublishedProject } from "@/lib/projects/items";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const project = await getPublishedProject(slug);

  if (!project) {
    return createPublicMetadata({
      title: "Project | AI Lab Portal",
      description: "AI Lab project.",
      path: `/projects/${slug}`,
    });
  }

  return createPublicMetadata({
    title: `${project.title} | AI Lab Portal`,
    description: project.description,
    ogImageUrl: project.imageUrl ?? undefined,
    path: `/projects/${slug}`,
  });
}

export default async function ProjectDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const [{ slug }, session] = await Promise.all([
    params,
    auth.api.getSession({ headers: await headers() }),
  ]);
  const project = await getPublishedProject(slug);

  if (!project) {
    notFound();
  }

  return (
    <PublicPageShell currentPath="/projects">
      <article className={cn(publicMainWidthClass, "flex flex-col gap-10 sm:gap-12")}>
        <div className="flex items-start justify-between gap-4">
          <PublicBackLink href="/projects">Projects</PublicBackLink>

          {session && (
            <Link
              className={cn(buttonVariants({ variant: "outline", size: "sm" }), "shrink-0")}
              href={`/admin/projects/${project.id}/edit`}
            >
              <Pencil className="size-3.5 shrink-0" />
              Edit
            </Link>
          )}
        </div>

          <PublicArticleHeader
            dateLabel={new Date(project.publishedAt).toLocaleDateString("en-US", {
            month: "long",
            day: "numeric",
            year: "numeric",
          })}
          eyebrow="Company project"
          excerpt={project.description}
            title={project.title}
          />

          {project.imageUrl && (
            <div className="relative aspect-[16/9] w-full overflow-hidden rounded-[1.5rem] border border-border/80 bg-muted shadow-[0_24px_60px_color-mix(in_srgb,var(--primary)_7%,transparent)]">
              <Image
                alt=""
                className="object-cover"
                fill
                priority
                src={project.imageUrl}
                unoptimized
              />
            </div>
          )}

          <PublicProse contentMarkdown={project.contentMarkdown} />
      </article>
    </PublicPageShell>
  );
}
