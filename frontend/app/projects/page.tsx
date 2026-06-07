import { PublicIndexEntry } from "@/components/public/public-index-entry";
import { PublicIndexList } from "@/components/public/public-index-list";
import { PublicPageHero } from "@/components/public/public-page-hero";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { listPublishedProjects } from "@/lib/projects/items";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { cn } from "@/lib/utils";

export const metadata = createPublicMetadata({
  title: "Our Projects | AI Lab Portal",
  description: "Company projects and initiatives showcasing AI Lab engineering work.",
  path: "/projects",
});

// ISR: project list is stable; revalidate every 5 minutes.
export const revalidate = 300;

export default async function ProjectsIndexPage() {
  const projects = await listPublishedProjects();

  return (
    <PublicPageShell currentPath="/projects">
      <section className={cn(publicMainWidthClass, "flex flex-col gap-14 sm:gap-16 lg:gap-20")}>
        <PublicPageHero
          description="Published projects explain how AI Lab builds practical solutions. Draft work stays private."
          eyebrow="Our Projects"
          title="Engineering initiatives with impact."
        />

        <PublicIndexList
          emptyDescription="Published projects will appear here after an admin publishes them."
          emptyTitle="No published projects yet"
          isEmpty={projects.length === 0}
        >
          {projects.map((project) => (
            <PublicIndexEntry
              key={project.slug}
                excerpt={project.description}
                href={`/projects/${project.slug}`}
                imageUrl={project.imageUrl ?? undefined}
                meta={new Date(project.publishedAt).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                year: "numeric",
              })}
              title={project.title}
            />
          ))}
        </PublicIndexList>
      </section>
    </PublicPageShell>
  );
}
