"use client";

import type { ReactNode } from "react";

import { motion, useReducedMotion } from "framer-motion";
import { FileText } from "lucide-react";

import { publicFadeIn } from "@/components/public/public-motion";
import { publicEmptyStateClass, publicMetaClass } from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

type PublicEmptyStateProps = {
  description: string;
  icon?: ReactNode;
  title: string;
};

export function PublicEmptyState({ description, icon, title }: PublicEmptyStateProps) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.div
      className={cn(publicEmptyStateClass, "relative overflow-hidden")}
      initial={reduceMotion ? false : "hidden"}
      animate="show"
      variants={publicFadeIn}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_70%_50%_at_50%_0%,color-mix(in_srgb,var(--brand)_10%,transparent),transparent_70%)]"
      />
      <div className="relative">
        <span className="mx-auto flex size-12 items-center justify-center rounded-2xl border border-border/90 bg-card text-brand">
          {icon ?? <FileText className="size-5" aria-hidden />}
        </span>
        <h2 className="mt-5 font-(family-name:--font-gt-super) text-2xl font-normal tracking-[-0.03em] text-foreground">
          {title}
        </h2>
        <p className={cn(publicMetaClass, "mx-auto mt-3 max-w-md leading-7")}>{description}</p>
      </div>
    </motion.div>
  );
}
