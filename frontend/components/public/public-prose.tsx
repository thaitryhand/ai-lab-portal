"use client";

import { motion } from "framer-motion";

import { MarkdownContent } from "@/components/public/markdown-content";
import { publicFadeUp } from "@/components/public/public-motion";
import { publicProseMeasureClass } from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

type PublicProseProps = {
  className?: string;
  contentMarkdown: string;
};

export function PublicProse({ className, contentMarkdown }: PublicProseProps) {
  return (
    <motion.div
      className={cn(
        "border-t border-border/80 bg-linear-to-b from-card/40 to-transparent px-1 pt-10 sm:px-2 sm:pt-12 lg:px-4",
        className
      )}
      initial={false}
      animate="show"
      variants={publicFadeUp}
    >
      <div className={publicProseMeasureClass}>
        <MarkdownContent markdown={contentMarkdown} />
      </div>
    </motion.div>
  );
}
