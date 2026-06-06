"use client";

import Image from "next/image";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowUpRight, Clock3 } from "lucide-react";
import type { ReactNode } from "react";

import { publicStaggerItem } from "@/components/public/public-motion";
import {
  publicEntryExcerptClass,
  publicEntryTitleClass,
  publicListRowClass,
  publicMetaClass,
} from "@/components/public/public-ui";
import { PublicBookmarkButton } from "@/components/public/public-bookmark-button";
import { cn } from "@/lib/utils";

type PublicIndexEntryProps = {
  excerpt: string;
  href: string;
  imageUrl?: string;
  meta: ReactNode;
  title: string;
  readingTimeLabel?: string;
  /** Enable bookmark button on this entry */
  showBookmark?: boolean;
  slug?: string;
};

export function PublicIndexEntry({
  excerpt,
  href,
  imageUrl,
  meta,
  title,
  readingTimeLabel,
  showBookmark,
  slug,
}: PublicIndexEntryProps) {
  const reduceMotion = useReducedMotion();

  // Derive slug from href if not provided
  const entrySlug = slug ?? (href.startsWith("/blog/") ? href.replace("/blog/", "") : undefined);

  return (
    <motion.article variants={reduceMotion ? undefined : publicStaggerItem}>
      <Link className={cn(publicListRowClass, "group")} href={href}>
        <div
          className={cn(
            "grid gap-6",
            imageUrl ? "sm:grid-cols-[10rem_minmax(0,1fr)_auto] sm:items-start" : "grid-cols-[minmax(0,1fr)_auto] items-start",
          )}
        >
          {imageUrl && (
            <div className="relative aspect-[16/10] min-h-36 overflow-hidden rounded-xl border border-border/80 bg-muted sm:mt-1 sm:aspect-[4/3] sm:min-h-0">
              <Image
                alt=""
                className="object-cover transition-transform duration-500 group-hover:scale-[1.03]"
                fill
                loading="lazy"
                src={imageUrl}
                unoptimized
              />
            </div>
          )}

          <div className="min-w-0">
            <p className={cn(publicMetaClass, "flex flex-wrap items-center gap-1.5")}>
              {meta}
              {readingTimeLabel ? (
                <>
                  <span aria-hidden>·</span>
                  <span className="inline-flex items-center gap-1">
                    <Clock3 className="size-3" aria-hidden />
                    {readingTimeLabel}
                  </span>
                </>
              ) : null}
            </p>
            <h2 className={cn(publicEntryTitleClass, "mt-2.5")}>{title}</h2>
            <p className={publicEntryExcerptClass}>{excerpt}</p>
          </div>

          <div className="flex items-start justify-end gap-2">
            {showBookmark && entrySlug && (
              <span
                className="relative z-10"
                onClick={(e) => e.stopPropagation()}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    e.stopPropagation();
                  }
                }}
                role="presentation"
              >
                <PublicBookmarkButton slug={entrySlug} />
              </span>
            )}
            <span
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-border/90 text-muted-foreground transition-[border-color,background-color,transform,color] duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:border-brand/35 group-hover:bg-accent group-hover:text-brand"
              aria-hidden
            >
              <ArrowUpRight className="size-4" />
            </span>
          </div>
        </div>
      </Link>
    </motion.article>
  );
}
