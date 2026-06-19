"use client";

import Link from "next/link";
import { useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import { Menu, X } from "lucide-react";
import { publicFadeIn } from "@/components/public/public-motion";
import { BrandMark } from "@/components/brand/brand-mark";
import {
  publicDisplayTitleClass,
  publicEyebrowClass,
  publicLandingHeaderClass,
} from "@/components/public/public-ui";
import { PublicUserMenu } from "@/components/public/public-user-menu";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type NavItem = { href: string; label: string; featured?: boolean };

const navItems: NavItem[] = [
  { href: "/tour", label: "Tour", featured: true },
  { href: "/lab", label: "AI Lab" },
  { href: "/showcases", label: "Showcases" },
  { href: "/projects", label: "Projects" },
  { href: "/blog", label: "Blog" },
  { href: "/ai-news", label: "AI News" },
];

type PublicLandingHeaderProps = {
  currentPath?: string;
};

export function PublicLandingHeader({ currentPath }: PublicLandingHeaderProps) {
  const reduceMotion = useReducedMotion();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
      <Link className="group flex min-w-0 shrink-0 items-center gap-2 transition-transform duration-200 hover:scale-[1.01] sm:gap-3" href="/">
        <BrandMark size="lg" />
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
        {/* Desktop nav */}
        <nav
          aria-label="Public navigation"
          className="hidden items-center gap-1 overflow-x-auto px-0.5 py-1 text-sm font-semibold [-ms-overflow-style:none] scrollbar-none [&::-webkit-scrollbar]:hidden md:flex md:gap-2"
        >
          {navItems.map((item) => {
            const isActive = currentPath === item.href;
            return (
              <Link
                key={item.href}
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "shrink-0 rounded-full px-4 py-1.5 text-sm font-semibold tracking-tight transition-all duration-200",
                  item.featured && !isActive
                    ? "bg-brand/12 text-brand ring-1 ring-brand/30 hover:bg-brand hover:text-white hover:ring-brand"
                    : isActive
                      ? "bg-brand/10 text-brand shadow-sm ring-1 ring-brand/25"
                      : "text-muted-foreground/70 hover:bg-muted/60 hover:text-foreground"
                )}
                href={item.href}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Mobile hamburger — visible below md */}
        <div className="relative md:hidden">
          <Button
            variant="ghost"
            size="icon"
            className="h-10 w-10 rounded-full"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
          >
            {mobileMenuOpen ? <X className="size-4" /> : <Menu className="size-4" />}
          </Button>

          {mobileMenuOpen && (
            <>
              {/* Backdrop */}
              <div
                className="fixed inset-0 z-40"
                onClick={() => setMobileMenuOpen(false)}
                aria-hidden
              />
              {/* Dropdown panel */}
              <nav
                aria-label="Mobile navigation"
                className="absolute right-0 top-full z-50 mt-2 w-48 overflow-hidden rounded-2xl border border-border/50 bg-card shadow-[0_8px_32px_rgba(0,0,0,0.12)] backdrop-blur-sm"
              >
                {navItems.map((item) => {
                  const isActive = currentPath === item.href;
                  return (
                    <Link
                      key={item.href}
                      aria-current={isActive ? "page" : undefined}
                      className={cn(
                        "flex items-center px-5 py-3 text-sm font-semibold transition-colors",
                        item.featured && !isActive
                          ? "text-brand"
                          : isActive
                            ? "bg-brand/10 text-brand"
                            : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
                      )}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      {item.label}
                    </Link>
                  );
                })}
                {/* Mobile-only auth links */}
                <div className="border-t border-border/40 px-5 py-4">
                  <Link
                    href="/login"
                    className="flex items-center px-0 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/register"
                    className="flex items-center px-0 py-2.5 text-sm font-medium text-brand hover:text-brand/80 transition-colors"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    Create account
                  </Link>
                </div>
              </nav>
            </>
          )}
        </div>

        {/* Desktop user menu (hidden on mobile — shown in hamburger panel) */}
        <div className="hidden md:block">
          <PublicUserMenu />
        </div>
      </div>
    </motion.header>
  );
}
