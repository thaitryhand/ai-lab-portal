"use client";

import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

import { publicFadeUp } from "@/components/public/public-motion";
import {
  publicArticleTitleClass,
  publicEyebrowClass,
  publicMetaClass,
  publicProseMeasureClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

type PublicArticleHeaderProps = {
  dateLabel: string;
  eyebrow: ReactNode;
  excerpt: string;
  title: string;
  readingTimeLabel?: string;
};

export function PublicArticleHeader({ dateLabel, eyebrow, excerpt, title, readingTimeLabel }: PublicArticleHeaderProps) {
  const reduceMotion = useReducedMotion();

  return (
      <motion.header
        className="relative border-b border-border/80 pb-10 sm:pb-12"
      custom={1}
      initial={reduceMotion ? false : "hidden"}
      animate="show"
      variants={publicFadeUp}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute -left-4 top-0 hidden h-full w-px bg-linear-to-b from-brand/60 via-brand/20 to-transparent sm:block"
      />
        <p className={publicEyebrowClass}>{eyebrow}</p>
        <p className={cn(publicMetaClass, "mt-4 flex flex-wrap items-center gap-1.5")}>
          <span>{dateLabel}</span>
        {readingTimeLabel ? (
          <>
            <span aria-hidden>·</span>
            <span>{readingTimeLabel}</span>
          </>
        ) : null}
      </p>
        <h1 className={cn(publicArticleTitleClass, "mt-5 sm:mt-6")}>{title}</h1>
        <p className={cn(publicProseMeasureClass, "mt-7 text-lg leading-8 text-muted-foreground sm:mt-9 sm:text-xl sm:leading-9")}>
          {excerpt}
        </p>
    </motion.header>
  );
}
