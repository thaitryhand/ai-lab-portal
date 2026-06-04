import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export default function ProjectsLoading() {
  return (
    <PublicPageShell currentPath="/projects">
      <section className={cn(publicMainWidthClass, "flex flex-col gap-14 sm:gap-16 lg:gap-20")}>
        <div className="flex flex-col gap-3">
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-10 w-3/4" />
          <Skeleton className="h-5 w-1/2" />
        </div>

        <div className="flex flex-col gap-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-1.5 border-b border-border pb-5">
              <Skeleton className="h-3 w-1/3" />
              <Skeleton className="mt-2 h-6 w-2/3" />
              <Skeleton className="mt-1 h-4 w-full" />
            </div>
          ))}
        </div>
      </section>
    </PublicPageShell>
  );
}
