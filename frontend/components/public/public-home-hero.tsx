"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Briefcase,
  CheckCircle2,
  FileText,
  FlaskConical,
  Globe,
  PenLine,
  ShieldCheck,
} from "lucide-react";

import {
  publicEyebrowClass,
  publicGhostCtaClass,
  publicHeroPanelClass,
  publicHeroTitleClass,
  publicLeadClass,
  publicPanelGridGapClass,
  publicPanelPaddingClass,
  publicPrimaryCtaClass,
  publicSecondaryCtaClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

const publishSteps = [
  {
    icon: PenLine,
    title: "Draft",
    description: "Compose in the CMS with rich text and metadata.",
  },
  {
    icon: ShieldCheck,
    title: "Review",
    description: "An authenticated admin approves before anything goes public.",
  },
  {
    icon: Globe,
    title: "Publish",
    description: "Live on lab, blog, and showcases.",
  },
] as const;

const liveSurfaces = [
  {
    icon: FlaskConical,
    title: "AI Lab",
    href: "/lab",
    detail: "Positioning, principles, and public focus.",
  },
  {
    icon: Briefcase,
    title: "Showcases",
    href: "/showcases",
    detail: "Client stories with outcomes and context.",
  },
  {
    icon: BookOpen,
    title: "Blog",
    href: "/blog",
    detail: "Engineering notes after human review.",
  },
] as const;

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, delay: 0.12 + i * 0.09, ease: [0.16, 1, 0.3, 1] as const },
  }),
};

export function PublicHomeHero() {
  const reduceMotion = useReducedMotion();

  return (
    <section className={publicHeroPanelClass}>
      <div
        aria-hidden
        className="pointer-events-none absolute -left-8 top-1/2 h-48 w-48 -translate-y-1/2 rounded-full bg-brand/6 blur-3xl sm:-left-12"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute right-8 top-8 hidden h-24 w-px bg-linear-to-b from-brand/50 via-brand/20 to-transparent lg:block"
      />

      <div
        className={cn(
          "relative grid lg:grid-cols-[minmax(0,1.12fr)_minmax(18rem,0.88fr)]",
          publicPanelPaddingClass,
          publicPanelGridGapClass
        )}
      >
        <motion.div
          className="max-w-3xl min-w-0 lg:pr-4 xl:pr-8"
          custom={0}
          initial={reduceMotion ? false : "hidden"}
          animate="show"
          variants={fadeUp}
        >
            <div className="inline-flex items-center gap-2 rounded-full border border-brand/25 bg-accent px-3 py-1">
              <span className="h-1.5 w-1.5 rounded-full bg-brand" aria-hidden />
              <p className={cn(publicEyebrowClass, "tracking-[0.18em] sm:tracking-[0.26em]")}>MVP 1 · Manual CMS</p>
            </div>

            <h1 className={cn(publicHeroTitleClass, "mt-8 sm:mt-10")}>
            A credible AI Lab presence with{" "}
            <span className="text-brand">human review</span> at the center.
          </h1>

            <p className={cn(publicLeadClass, "mt-6 sm:mt-10")}>
              Publish blog articles and client showcases manually. Drafts stay private until an authenticated admin
              approves what goes live.
            </p>

          <div className="mt-12 flex flex-col gap-4 sm:mt-14 sm:flex-row sm:flex-wrap sm:items-center">
            <Link className={cn(publicPrimaryCtaClass, "group")} href="/lab">
              Explore AI Lab
              <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" aria-hidden />
            </Link>
            <Link className={publicSecondaryCtaClass} href="/showcases">
              View showcases
            </Link>
            <Link className={publicGhostCtaClass} href="/blog">
              Read the blog
            </Link>
          </div>

          <dl className="mt-12 grid grid-cols-3 gap-5 border-t border-border/70 pt-8 sm:mt-14 sm:max-w-lg sm:gap-6 sm:pt-10">
            {[
              { label: "Surfaces", value: "3 live" },
              { label: "Review", value: "Human-first" },
              { label: "CMS", value: "Manual" },
            ].map((stat) => (
              <div key={stat.label}>
                <dt className="text-[10px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                  {stat.label}
                </dt>
                <dd className="mt-1.5 font-(family-name:--font-gt-super) text-xl tracking-[-0.03em] text-foreground">
                  {stat.value}
                </dd>
              </div>
            ))}
          </dl>
        </motion.div>

        <motion.aside
          className="relative min-w-0 lg:border-l lg:border-border/70 lg:pl-12 xl:pl-16"
          custom={1}
          initial={reduceMotion ? false : "hidden"}
          animate="show"
          variants={fadeUp}
          >
            <div className="overflow-hidden rounded-2xl border border-border/70 bg-background/75 shadow-[0_24px_60px_color-mix(in_srgb,var(--primary)_7%,transparent)]">
              <div className="border-b border-border/65 bg-muted/35 px-5 py-4 sm:px-6">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      CMS review snapshot
                    </p>
                    <p className="mt-1 text-sm font-semibold text-foreground">Human-reviewed publish queue</p>
                  </div>
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-brand/25 bg-accent px-3 py-1 text-xs font-semibold text-brand">
                    <CheckCircle2 className="size-3.5" aria-hidden />
                    Approved
                  </span>
                </div>
              </div>

              <div className="grid gap-5 p-5 sm:p-6 lg:p-7">
                <div className="rounded-xl border border-border/65 bg-card p-4">
                  <div className="flex items-start gap-3">
                    <span className="flex size-9 shrink-0 items-center justify-center rounded-lg border border-brand/20 bg-accent text-brand">
                      <FileText className="size-4" aria-hidden />
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-foreground">Operational note ready for public blog</p>
                      <p className="mt-2 text-sm leading-6 text-muted-foreground">
                        Draft, SEO metadata, and reviewer notes stay visible before publish.
                      </p>
                    </div>
                  </div>
                </div>

                <ol className="grid gap-3">
                  {publishSteps.map((step) => {
                    const Icon = step.icon;
                    return (
                      <li key={step.title} className="flex items-center gap-3 text-sm">
                        <span className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-border/70 bg-muted/30 text-brand">
                          <Icon className="size-3.5" aria-hidden />
                        </span>
                        <span className="min-w-0">
                          <span className="font-semibold text-foreground">{step.title}</span>
                          <span className="ml-2 text-muted-foreground">{step.description}</span>
                        </span>
                      </li>
                    );
                  })}
                </ol>

                <div className="grid grid-cols-3 gap-2 border-t border-border/60 pt-5 text-center">
                  {[
                    ["Draft", "Private"],
                    ["Gate", "Admin"],
                    ["Output", "Public"],
                  ].map(([label, value]) => (
                    <div key={label} className="min-w-0">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                        {label}
                      </p>
                      <p className="mt-1 font-(family-name:--font-gt-super) text-lg leading-none text-foreground">
                        {value}
                      </p>
                    </div>
                  ))}
                </div>

                <div className="border-t border-border/60 pt-3.5">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-[9px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                      Live surfaces
                    </p>
                    <span className="rounded-full border border-brand/20 bg-accent px-2 py-px text-[9px] font-semibold uppercase tracking-[0.12em] text-brand">
                      3 live
                    </span>
                  </div>

                  <ul className="mt-2 grid gap-1">
                    {liveSurfaces.map((surface) => {
                      const Icon = surface.icon;
                      return (
                        <li key={surface.title}>
                          <Link
                            href={surface.href}
                            className="group flex items-center gap-2 rounded-lg border border-transparent px-2 py-1.5 transition-[border-color,background-color] duration-200 hover:border-brand/20 hover:bg-muted/35"
                          >
                            <span className="flex size-6 shrink-0 items-center justify-center rounded-md border border-border/70 bg-card text-brand transition-colors group-hover:border-brand/30 group-hover:bg-accent">
                              <Icon className="size-3" aria-hidden />
                            </span>
                            <span className="min-w-0 flex-1">
                              <span className="block text-xs font-semibold leading-4 text-foreground transition-colors group-hover:text-brand">
                                {surface.title}
                              </span>
                              <span className="block truncate text-[11px] leading-4 text-muted-foreground">
                                {surface.detail}
                              </span>
                            </span>
                            <ArrowUpRight
                              className="size-3 shrink-0 text-muted-foreground/60 transition-[transform,color] group-hover:translate-x-px group-hover:-translate-y-px group-hover:text-brand"
                              aria-hidden
                            />
                          </Link>
                        </li>
                      );
                    })}
                  </ul>

                  <div className="mt-2.5 flex items-start gap-2 rounded-lg border border-dashed border-border/60 bg-muted/15 px-2.5 py-2">
                    <ShieldCheck className="mt-px size-3 shrink-0 text-brand" aria-hidden />
                    <div className="min-w-0">
                      <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                        Editorial assurance
                      </p>
                      <p className="mt-0.5 text-[11px] leading-4 text-foreground">
                        Every public page passes the same human review gate — no auto-publish, no draft leakage.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.aside>
      </div>
    </section>
  );
}
