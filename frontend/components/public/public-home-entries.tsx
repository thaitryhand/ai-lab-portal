"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowUpRight, BookOpen, Briefcase, FlaskConical } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import {
  publicEyebrowClass,
  publicLandingSectionGap,
  publicSectionHeaderBlockClass,
  publicSectionIntroGapClass,
  publicSectionTitleClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

type Entry = {
  description: string;
  detail: string;
  href: string;
  icon: LucideIcon;
  index: string;
  title: string;
};

const entries: Entry[] = [
  {
    index: "01",
    title: "AI Lab",
    description: "The overview layer for positioning, principles, and what the lab is building in public.",
    detail: "Mission, operating model, and current focus areas.",
    href: "/lab",
    icon: FlaskConical,
  },
  {
    index: "02",
    title: "Showcases",
    description: "Client-ready delivery stories with industry context, outcomes, and publish controls.",
    detail: "Proof of work without exposing private drafts.",
    href: "/showcases",
    icon: Briefcase,
  },
  {
    index: "03",
    title: "Blog",
    description: "Practical AI engineering notes, workflow lessons, and human-reviewed field reports.",
    detail: "Editorial posts approved before they go public.",
    href: "/blog",
    icon: BookOpen,
  },
];

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] as const },
  }),
};

function EntryCard({ entry, index }: { entry: Entry; index: number }) {
  const Icon = entry.icon;

  return (
    <motion.div custom={index} initial="hidden" animate="show" variants={fadeUp} className="h-full">
      <Link
        className="group relative flex h-full min-h-[18rem] flex-col overflow-hidden rounded-[1.75rem] border border-border/80 bg-card/95 p-8 shadow-[0_20px_50px_color-mix(in_srgb,var(--primary)_5%,transparent)] transition-[transform,box-shadow,border-color,background-color] duration-300 hover:-translate-y-1 hover:border-brand/30 hover:bg-card hover:shadow-[0_28px_60px_color-mix(in_srgb,var(--brand)_12%,transparent)] sm:p-9 lg:p-10"
        href={entry.href}
      >
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 top-0 h-px bg-linear-to-r from-transparent via-brand/45 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute -right-12 -top-12 h-40 w-40 rounded-full bg-brand/6 blur-3xl transition-opacity duration-300 group-hover:bg-brand/12"
        />

        <div className="relative flex items-start justify-between gap-6">
          <span className="font-(family-name:--font-gt-super) text-5xl leading-none text-brand/75 tabular-nums">
            {entry.index}
          </span>
          <span className="flex size-12 items-center justify-center rounded-2xl border border-border/80 bg-muted/50 text-muted-foreground transition-[background-color,color,border-color] duration-300 group-hover:border-brand/25 group-hover:bg-accent group-hover:text-brand">
            <Icon className="size-5" aria-hidden />
          </span>
        </div>

        <div className="relative mt-8 flex flex-1 flex-col sm:mt-9">
          <h3 className="font-(family-name:--font-gt-super) text-3xl font-normal tracking-[-0.04em] text-foreground transition-colors group-hover:text-brand sm:text-4xl">
            {entry.title}
          </h3>
          <p className="mt-4 max-w-md text-base leading-7 text-muted-foreground">
            {entry.description}
          </p>

          <div className="mt-auto pt-7 sm:pt-8">
            <div className="rounded-2xl border border-border/55 bg-background/35 px-4 py-3 text-sm leading-6 text-muted-foreground">
              {entry.detail}
            </div>
            <span className="mt-6 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground transition-colors group-hover:text-brand">
              Open
              <ArrowUpRight className="size-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" aria-hidden />
            </span>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}

export function PublicHomeEntries() {
  const reduceMotion = useReducedMotion();

  return (
    <section className={publicLandingSectionGap} aria-labelledby="explore-heading">
      <div className={publicSectionHeaderBlockClass}>
        <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between lg:gap-16">
          <div className="max-w-xl">
            <p className={publicEyebrowClass}>Explore</p>
            <h2 id="explore-heading" className={cn(publicSectionTitleClass, publicSectionIntroGapClass)}>
              Start here
            </h2>
          </div>
          <p className="max-w-sm text-base leading-7 text-muted-foreground lg:pb-1 lg:text-right">
            Three public surfaces. One editorial standard for everything that ships.
          </p>
        </div>
      </div>

      <div className="grid gap-5 sm:gap-6 lg:grid-cols-3">
        {entries.map((entry, index) => (
          <EntryCard key={entry.href} entry={entry} index={reduceMotion ? 0 : index} />
        ))}
      </div>
    </section>
  );
}
