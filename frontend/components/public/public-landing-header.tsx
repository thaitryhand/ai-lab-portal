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
import { PublicUserMenu } from "@/components/public/public-user-menu";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/lab", label: "AI Lab" },
  { href: "/showcases", label: "Showcases" },
  { href: "/projects", label: "Projects" },
  { href: "/blog", label: "Blog" },
  { href: "/ai-news", label: "AI News" },
] as const;

type PublicLandingHeaderProps = {
  currentPath?: string;
};

export function PublicLandingHeader({ currentPath }: PublicLandingHeaderProps) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.header
      className={cn(
        publicLandingHeaderClass,
        "flex-wrap gap-3 sm:flex-nowrap"
      )}
      initial={reduceMotion ? false : "hidden"}
      animate="show"
      variants={publicFadeIn}
    >
      {/* Logo */}
      <Link className="group flex min-w-0 shrink-0 items-center gap-3 sm:gap-4" href="/">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-brand/30 bg-accent text-brand shadow-sm transition-transform duration-200 group-hover:scale-[1.02] sm:h-11 sm:w-11">
          <PenLine className="size-3.5 sm:size-4" aria-hidden />
        </span>
        <span className="min-w-0">
          <span className={cn(publicEyebrowClass, "text-[10px] sm:text-[11px]")}>AI Lab Portal</span>
          <span
            className={cn(
              publicDisplayTitleClass,
              "mt-0.5 block truncate text-sm transition-colors group-hover:text-brand sm:text-base"
            )}
          >
            Editorial AI engineering
          </span>
        </span>
      </Link>

      {/* Right section: nav + user menu */}
      <div className="flex flex-1 items-center justify-end gap-2">
        <nav
          aria-label="Public navigation"
          className="hidden items-center gap-1 overflow-x-auto pb-0.5 text-sm font-semibold [-ms-overflow-style:none] scrollbar-none [&::-webkit-scrollbar]:hidden md:flex md:gap-2"
        >
          {navItems.map((item) => {
            const isActive = currentPath === item.href;
            return (
              <Link
                key={item.href}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "shrink-0 rounded-full px-3 py-2 text-sm transition-[background-color,color] duration-200",
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
        </nav>

        {/* Mobile nav toggle - show first 2 items */}
        <nav
          aria-label="Quick navigation"
          className="flex items-center gap-1 md:hidden"
        >
          {navItems.slice(0, 2).map((item) => {
            const isActive = currentPath === item.href;
            return (
              <Link
                key={item.href}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "shrink-0 rounded-full px-2.5 py-1.5 text-xs font-semibold transition-[background-color,color] duration-200",
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
        </nav>

        <PublicUserMenu />
      </div>
    </motion.header>
  );
}
