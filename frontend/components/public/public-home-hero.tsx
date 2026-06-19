"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Briefcase,
  CheckCircle2,
  FlaskConical,
  Globe,
  Layers,
  PenLine,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

import {
  publicEyebrowClass,
  publicHeroPanelClass,
  publicHeroTitleClass,
  publicLeadClass,
  publicPanelGridGapClass,
  publicPanelPaddingClass,
  publicPrimaryCtaClass,
  publicSecondaryCtaClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

const pipelineStages = [
  { icon: Sparkles, label: "Idea" },
  { icon: Layers, label: "Outline" },
  { icon: PenLine, label: "Draft" },
  { icon: ShieldCheck, label: "Review" },
  { icon: Globe, label: "Publish" },
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
    detail: "AI-generated, human-reviewed engineering notes.",
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
            <div className="inline-flex items-center gap-2 rounded-full border border-brand/25 bg-accent px-3 py-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-brand" aria-hidden />
            <p className={cn(publicEyebrowClass, "font-medium tracking-[0.18em] sm:tracking-[0.26em]")}>AI Lab Platform</p>
          </div>

          <h1 className={cn(publicHeroTitleClass, "mt-8 sm:mt-10")}>
            From project to published —{" "}
            <span className="text-brand">powered by AI</span>, reviewed by humans.
          </h1>

          <p className={cn(publicLeadClass, "mt-6 sm:mt-10")}>
            A seven-stage semi-auto pipeline generates blog ideas, outlines, drafts,
            technical reviews, and marketing metadata — with a human gate at every step.
            No auto-publish, no black boxes.
          </p>

          <div className="mt-12 flex flex-col gap-4 sm:mt-14 sm:flex-row sm:flex-wrap sm:items-center">
            <Link className={cn(publicPrimaryCtaClass, "group")} href="/tour">
              Take the Tour
              <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" aria-hidden />
            </Link>
            <Link className={publicSecondaryCtaClass} href="/lab">
              Explore the AI Lab
            </Link>
            <Link className={cn(publicSecondaryCtaClass, "border-brand/30 bg-brand/8 text-brand hover:bg-brand/12 hover:border-brand/40")} href="/blog">
              Read the blog
            </Link>
          </div>

          <dl className="mt-12 grid grid-cols-3 gap-5 border-t border-border/70 pt-8 sm:mt-14 sm:max-w-lg sm:gap-6 sm:pt-10">
            {[
              { label: "Pipeline stages", value: "7" },
              { label: "Review", value: "Human gates" },
              { label: "Published", value: "98+ stories" },
            ].map((stat) => (
              <div key={stat.label}>
                <dt className="text-[10px] font-medium uppercase tracking-[0.22em] text-muted-foreground">
                  {stat.label}
                </dt>
                <dd className="mt-2 font-(family-name:--font-gt-super) text-xl tracking-[-0.03em] text-foreground">
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
                    AI Pipeline
                  </p>
                  <p className="mt-1 text-sm font-semibold text-foreground">Semi-auto generation workflow</p>
                </div>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-brand/25 bg-accent px-3 py-1 text-xs font-semibold text-brand">
                  <CheckCircle2 className="size-3.5" aria-hidden />
                  Live demo
                </span>
              </div>
            </div>

            <div className="grid gap-5 p-5 sm:p-6 lg:p-7">
              {/* Pipeline stages */}
              <div className="rounded-xl border border-border/65 bg-card p-4">
                <div className="flex items-start gap-3">
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-lg border border-brand/20 bg-accent text-brand">
                    <Sparkles className="size-4" aria-hidden />
                  </span>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-foreground">AI-powered pipeline</p>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">
                      Project context → Idea → Outline → Draft → Review → Marketing → Publish.
                    </p>
                  </div>
                </div>
              </div>

              <ol className="grid gap-3">
                {pipelineStages.map((step) => {
                  const Icon = step.icon;
                  return (
                    <li key={step.label} className="flex items-center gap-3 text-sm">
                      <span className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-border/70 bg-muted/30 text-brand">
                        <Icon className="size-3.5" aria-hidden />
                      </span>
                      <span className="min-w-0">
                        <span className="font-semibold text-foreground">{step.label}</span>
                        <span className="ml-2 text-muted-foreground">AI-generated, human-approved</span>
                      </span>
                    </li>
                  );
                })}
              </ol>

              <div className="grid grid-cols-3 gap-2 border-t border-border/60 pt-5 text-center">
                {[
                  ["Input", "Project"],
                  ["Gates", "7 human"],
                  ["Output", "Published"],
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
                    AI-generated
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

                <Link
                  href="/tour"
                  className="mt-2.5 flex items-start gap-2 rounded-lg border border-dashed border-brand/30 bg-brand/5 px-2.5 py-2 transition-colors hover:bg-brand/10"
                >
                  <Globe className="mt-px size-3 shrink-0 text-brand" aria-hidden />
                  <div className="min-w-0">
                    <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-brand">
                      See it in action
                    </p>
                    <p className="mt-0.5 text-[11px] leading-4 text-muted-foreground">
                      Watch the full 7-stage pipeline from project to published post →
                    </p>
                  </div>
                </Link>
              </div>
            </div>
          </div>
        </motion.aside>
      </div>
    </section>
  );
}
