"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Globe, PenLine, ShieldCheck } from "lucide-react";

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
          "py-14 sm:py-16 lg:py-20 xl:py-24",
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
            <p className={cn(publicEyebrowClass, "tracking-[0.26em]")}>MVP 1 · Manual CMS</p>
          </div>

          <h1 className={cn(publicHeroTitleClass, "mt-8 sm:mt-10")}>
            A credible AI Lab presence with{" "}
            <span className="text-brand">human review</span> at the center.
          </h1>

          <p className={cn(publicLeadClass, "mt-8 sm:mt-10")}>
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
          <div className="rounded-2xl border border-border/70 bg-muted/25 p-7 sm:p-9 lg:p-10">
            <p className="text-[10px] font-semibold uppercase tracking-[0.28em] text-muted-foreground">
              Publishing flow
            </p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              AI assists drafting. Humans decide what ships.
            </p>

            <ol className="relative mt-8 grid gap-0 sm:mt-10">
              {publishSteps.map((step, index) => {
                const Icon = step.icon;
                const isLast = index === publishSteps.length - 1;
                return (
                  <li key={step.title} className="relative flex gap-5 pb-8 last:pb-0 sm:pb-10">
                    {!isLast ? (
                      <span
                        aria-hidden
                        className="absolute left-5 top-10 bottom-0 w-px bg-linear-to-b from-brand/40 to-border"
                      />
                    ) : null}
                    <span className="relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-brand/20 bg-card text-brand shadow-sm">
                      <Icon className="size-4" aria-hidden />
                    </span>
                    <div className="min-w-0 pt-0.5">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                        Step {index + 1}
                      </p>
                      <p className="mt-0.5 font-semibold text-foreground">{step.title}</p>
                      <p className="mt-1.5 text-sm leading-6 text-muted-foreground">{step.description}</p>
                    </div>
                  </li>
                );
              })}
            </ol>
          </div>
        </motion.aside>
      </div>
    </section>
  );
}
