"use client";

import { motion, useReducedMotion } from "framer-motion";
import { CheckCircle2 } from "lucide-react";

import {
  publicEyebrowClass,
  publicLandingSectionGap,
  publicPanelPaddingClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

const standards = [
  {
    label: "Draft in the CMS",
    description: "Work starts private, structured, and easy to revise.",
  },
  {
    label: "Human review gate",
    description: "Every post or showcase gets an explicit approval pass.",
  },
  {
    label: "Publish when ready",
    description: "No auto-publishing: public content ships deliberately.",
  },
  {
    label: "Public by choice",
    description: "Only polished, useful artifacts make it to the surface.",
  },
] as const;

const fadeIn = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] as const } },
};

export function PublicHomeStandards() {
  const reduceMotion = useReducedMotion();

  return (
    <motion.section
      className={cn(
        publicLandingSectionGap,
        "relative overflow-hidden rounded-[2rem] border border-border/75 bg-card/90 shadow-[0_24px_70px_color-mix(in_srgb,var(--primary)_6%,transparent)]",
        publicPanelPaddingClass,
      )}
      initial={reduceMotion ? false : "hidden"}
      animate="show"
      variants={fadeIn}
      aria-label="Editorial standards"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-brand/8 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-10 top-0 h-px bg-linear-to-r from-transparent via-brand/45 to-transparent"
      />

      <div className="relative grid gap-10 lg:grid-cols-[0.9fr_1.35fr] lg:items-start lg:gap-14">
        <div className="max-w-md">
          <p className={publicEyebrowClass}>Editorial standard</p>
          <h2 className="mt-5 font-(family-name:--font-gt-super) text-4xl font-normal leading-[1.02] tracking-[-0.045em] text-foreground sm:text-5xl">
            Private by default. Public with intent.
          </h2>
          <p className="mt-6 text-base leading-7 text-muted-foreground">
            AI helps draft and organize the work, but the publishing flow stays deliberate: reviewed, approved, and useful before anything reaches readers.
          </p>
        </div>

        <ol className="grid gap-3 sm:grid-cols-2">
          {standards.map((item, index) => (
            <li
              key={item.label}
              className="group rounded-2xl border border-border/65 bg-background/35 p-5 transition-colors hover:border-brand/30 hover:bg-muted/25"
            >
              <div className="flex items-start gap-4">
                <span className="font-(family-name:--font-gt-super) text-2xl leading-none text-brand/75 tabular-nums">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="size-4 shrink-0 text-brand/75" aria-hidden />
                    <h3 className="text-sm font-semibold uppercase tracking-[0.16em] text-foreground">
                      {item.label}
                    </h3>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-muted-foreground">{item.description}</p>
                </div>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </motion.section>
  );
}
