"use client";

import Link from "next/link";
import { motion, useReducedMotion } from "framer-motion";
import { PenLine } from "lucide-react";

import { publicFadeIn } from "@/components/public/public-motion";
import {
  publicDisplayTitleClass,
  publicEyebrowClass,
  publicLandingHeaderClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/lab", label: "AI Lab" },
  { href: "/showcases", label: "Showcases" },
  { href: "/projects", label: "Projects" },
  { href: "/blog", label: "Blog" },
  { href: "/ai-news", label: "AI News" },
  { href: "/contact", label: "Contact" },
  { href: "/profile", label: "Profile" },
] as const;

type PublicLandingHeaderProps = {
  currentPath?: string;
};

export function PublicLandingHeader({ currentPath }: PublicLandingHeaderProps) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.header
      className={publicLandingHeaderClass}
      initial={reduceMotion ? false : "hidden"}
      animate="show"
      variants={publicFadeIn}
    >
      <Link className="group flex min-w-0 items-center gap-4" href="/">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-brand/30 bg-accent text-brand shadow-sm transition-transform duration-200 group-hover:scale-[1.02]">
          <PenLine className="size-4" aria-hidden />
        </span>
        <span className="min-w-0">
          <span className={publicEyebrowClass}>AI Lab Portal</span>
          <span
            className={cn(
              publicDisplayTitleClass,
              "mt-0.5 block truncate text-base transition-colors group-hover:text-brand sm:text-lg"
            )}
          >
            Editorial AI engineering
          </span>
        </span>
      </Link>

      <nav
        aria-label="Public navigation"
        className="flex items-center gap-1 overflow-x-auto pb-0.5 text-sm font-semibold [-ms-overflow-style:none] scrollbar-none [&::-webkit-scrollbar]:hidden sm:gap-2"
      >
        {navItems.map((item) => {
          const isActive = currentPath === item.href;
          return (
            <Link
              key={item.href}
              aria-current={isActive ? "page" : undefined}
              className={cn(
                "shrink-0 rounded-full px-4 py-2.5 transition-[background-color,color] duration-200",
                isActive
                  ? "bg-accent text-foreground ring-1 ring-brand/25"
                  : "text-muted-foreground hover:bg-muted/80 hover:text-foreground"
              )}
              href={item.href}
            >
              {item.label}
            </Link>
          );
        })}
        <Link
          className="ml-2 shrink-0 rounded-full border border-border bg-background px-5 py-2.5 text-foreground transition-colors hover:border-brand/40 hover:text-brand"
          href="/admin"
        >
          Admin
        </Link>
      </nav>
    </motion.header>
  );
}
