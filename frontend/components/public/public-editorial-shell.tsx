import Link from "next/link";
import type { ReactNode } from "react";

import { PublicAtmosphere } from "@/components/public/public-atmosphere";
import { PublicLandingHeader } from "@/components/public/public-landing-header";
import {
  publicLandingStackClass,
  publicPageMainClass,
  publicPageStackClass,
  publicShellContainerClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

type PublicEditorialShellProps = {
  children: ReactNode;
  currentPath?: string;
  variant?: "landing" | "page";
};

function PublicEditorialFooter() {
  return (
    <footer className="mt-28 w-full border-t border-border/80 pt-14 sm:mt-36 sm:pt-16 lg:mt-40">
      <div className="flex flex-col gap-10 sm:flex-row sm:items-end sm:justify-between">
        <p className="max-w-md text-sm leading-7 text-muted-foreground">
          Human-reviewed publishing for AI Lab articles and client showcases. Drafts stay private until an admin
          publishes.
        </p>
        <div className="flex flex-wrap gap-x-8 gap-y-3 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          <Link className="transition-colors hover:text-brand" href="/lab">
            AI Lab
          </Link>
          <Link className="transition-colors hover:text-brand" href="/showcases">
            Showcases
          </Link>
          <Link className="transition-colors hover:text-brand" href="/projects">
            Projects
          </Link>
          <Link className="transition-colors hover:text-brand" href="/blog">
            Blog
          </Link>
          <Link className="transition-colors hover:text-brand" href="/ai-news">
            AI News
          </Link>
          <Link className="transition-colors hover:text-brand" href="/contact">
            Blog
          </Link>
          <Link className="transition-colors hover:text-brand" href="/contact">
            Contact
            Blog
          </Link>
        </div>
      </div>
    </footer>
  );
}

/** Shared layout: header, main, and footer share one max-width + gutter container */
export function PublicEditorialShell({
  children,
  currentPath,
  variant = "page",
}: PublicEditorialShellProps) {
  const mainStackClass = variant === "landing" ? publicLandingStackClass : publicPageStackClass;
  const mainTopClass = variant === "landing" ? "mt-16 sm:mt-20 lg:mt-24" : "mt-16 sm:mt-20 lg:mt-24";

  return (
    <div className={cn(publicPageMainClass, "relative")}>
      <PublicAtmosphere />
      <div className={publicShellContainerClass}>
        <div className="w-full pt-6 sm:pt-10">
          <PublicLandingHeader currentPath={currentPath} />
        </div>
        <main className={cn(mainStackClass, mainTopClass, "w-full min-w-0")}>{children}</main>
        <PublicEditorialFooter />
      </div>
    </div>
  );
}
