"use client";

import Image from "next/image";
import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";
import type { ReactNode } from "react";

import { publicStaggerItem } from "@/components/public/public-motion";
import {
  publicEntryExcerptClass,
  publicEntryTitleClass,
  publicListRowClass,
  publicMetaClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

type PublicIndexEntryProps = {
  excerpt: string;
  href: string;
  imageUrl?: string;
  meta: ReactNode;
  title: string;
};

export function PublicIndexEntry({ excerpt, href, imageUrl, meta, title }: PublicIndexEntryProps) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.article variants={reduceMotion ? undefined : publicStaggerItem}>
      <Link className={cn(publicListRowClass, "group")} href={href}>
        <div className="flex items-start justify-between gap-6">
          <div className="flex min-w-0 flex-1 items-start gap-5">
            {imageUrl && (
              <div className="relative mt-1 h-16 w-24 shrink-0 overflow-hidden rounded-md border">
                <Image
                  alt=""
                  className="object-cover"
                  fill
                  loading="lazy"
                  src={imageUrl}
                  unoptimized
                />
              </div>
            )}
            <div className="min-w-0 flex-1">
              <p className={publicMetaClass}>{meta}</p>
              <h2 className={cn(publicEntryTitleClass, "mt-2.5")}>{title}</h2>
              <p className={publicEntryExcerptClass}>{excerpt}</p>
            </div>
          </div>
          <span
            className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-border/90 text-muted-foreground transition-[border-color,background-color,transform,color] duration-300 group-hover:border-brand/35 group-hover:bg-accent group-hover:text-brand group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
            aria-hidden
          >
            <ArrowUpRight className="size-4" />
          </span>
        </div>
      </Link>
    </motion.article>
  );
}
