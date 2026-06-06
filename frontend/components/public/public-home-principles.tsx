"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Eye, Scale, Sparkles } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import {
  publicEyebrowClass,
  publicLandingCardPaddingClass,
  publicLandingSectionGap,
  publicLeadClass,
  publicSectionHeaderBlockClass,
  publicSectionIntroGapClass,
  publicSectionTitleClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

const principles: Array<{
  description: string;
  icon: LucideIcon;
  title: string;
}> = [
  {
    icon: Sparkles,
    title: "AI assists, humans decide",
    description:
      "Models can draft outlines and copy. Nothing reaches the public site until a person approves it in the CMS.",
  },
  {
    icon: Scale,
    title: "Evidence over hype",
    description:
      "Articles and showcases describe real workflows, review gates, and delivery boundaries clients can verify.",
  },
  {
    icon: Eye,
    title: "Transparent surfaces",
    description:
      "Lab, blog, and showcases share one editorial tone. Drafts and internal review stay off the public web.",
  },
];

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, delay: i * 0.1, ease: [0.16, 1, 0.3, 1] as const },
  }),
};

export function PublicHomePrinciples() {
  const reduceMotion = useReducedMotion();

  return (
    <section className={publicLandingSectionGap} aria-labelledby="principles-heading">
      <div className={publicSectionHeaderBlockClass}>
        <p className={publicEyebrowClass}>Philosophy</p>
        <h2 id="principles-heading" className={cn(publicSectionTitleClass, publicSectionIntroGapClass)}>
          Built for credibility, not automation theater.
        </h2>
        <p className={cn(publicLeadClass, "mt-6 max-w-2xl")}>
          The portal treats publishing as an editorial act. Speed matters, but trust matters more.
        </p>
      </div>

        <div className="grid gap-8 border-y border-border/70 py-8 sm:gap-10 sm:py-10 lg:grid-cols-3 lg:gap-12">
          {principles.map((item, index) => {
            const Icon = item.icon;
            return (
              <motion.article
                key={item.title}
                className={cn(
                  "flex flex-col gap-6 border-border/70 lg:border-r lg:pr-10 lg:last:border-r-0 lg:last:pr-0",
                  publicLandingCardPaddingClass,
                  "p-0 sm:p-0 lg:p-0",
                )}
                custom={index}
                initial={reduceMotion ? false : "hidden"}
              animate="show"
              variants={fadeUp}
            >
              <span className="flex size-12 items-center justify-center rounded-2xl border border-brand/20 bg-accent text-brand">
                <Icon className="size-5" aria-hidden />
              </span>
              <div className="space-y-3">
                <h3 className="font-(family-name:--font-gt-super) text-2xl font-normal tracking-[-0.03em] text-foreground">
                  {item.title}
                </h3>
                <p className="text-base leading-7 text-muted-foreground">{item.description}</p>
              </div>
            </motion.article>
          );
        })}
      </div>
    </section>
  );
}
