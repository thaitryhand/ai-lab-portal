"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowRight, Mail, MessageSquare } from "lucide-react";

import {
  publicEyebrowClass,
  publicLandingSectionGap,
  publicLeadClass,
  publicPanelPaddingClass,
  publicPrimaryCtaClass,
  publicSecondaryCtaClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.16, 1, 0.3, 1] as const } },
};

export function PublicHomeCta() {
  const reduceMotion = useReducedMotion();

  return (
    <motion.section
      className={cn(
        publicLandingSectionGap,
        "relative overflow-hidden rounded-[2rem] border border-border/80 bg-primary text-primary-foreground",
        publicPanelPaddingClass
      )}
      initial={reduceMotion ? false : "hidden"}
      animate="show"
      variants={fadeUp}
      aria-labelledby="cta-heading"
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-brand/20 blur-3xl"
      />
      <div className="relative mx-auto max-w-2xl text-center">
        <p className={cn(publicEyebrowClass, "text-brand")}>Ready to explore</p>
        <h2
          id="cta-heading"
          className="mt-6 font-(family-name:--font-gt-super) text-3xl font-normal leading-[1.05] tracking-[-0.04em] text-primary-foreground sm:text-4xl lg:text-5xl"
        >
          See how human-reviewed publishing works in practice.
        </h2>
        <p className={cn(publicLeadClass, "mx-auto mt-7 text-primary-foreground/75 sm:mt-8")}>
          Start with the lab overview, browse client showcases, or read the latest engineering notes.
        </p>
        <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:mt-12 sm:flex-row sm:gap-5">
          <Link
            className={cn(
              publicPrimaryCtaClass,
              "group bg-primary-foreground text-primary! hover:bg-primary-foreground/90"
            )}
            href="/lab"
          >
            Explore AI Lab
            <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" aria-hidden />
          </Link>
          <Link
            className={cn(
              publicSecondaryCtaClass,
              "border-primary-foreground/25 bg-transparent text-primary-foreground hover:border-primary-foreground/50 hover:bg-primary-foreground/10"
            )}
            href="/contact"
          >
            <Mail className="size-4" />
            Get in touch
          </Link>
        </div>
      </div>
    </motion.section>
  );
}
