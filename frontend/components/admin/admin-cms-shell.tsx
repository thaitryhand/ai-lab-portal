"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { useReducedMotion } from "framer-motion";
import {
  Briefcase,
  ExternalLink,
  FileText,
  LayoutDashboard,
  Lightbulb,
  Link as LinkIcon,
  MessageSquare,
  Moon,
  Newspaper,
  PencilLine,
  PlusCircle,
  Rss,
  Sun,
} from "lucide-react";
import { useTheme } from "next-themes";

import { adminDisplayTitleClass } from "@/components/admin/admin-ui";
import { cn } from "@/lib/utils";

type NavKey = "dashboard" | "blog" | "editor" | "projects" | "project-editor" | "showcases" | "showcase-editor" | "ideas" | "news" | "news-review" | "submitted-links" | "blog-comments";

type Props = { active: NavKey; children: ReactNode };

const navItems: Array<{ key: NavKey; href: string; label: string; icon: ReactNode }> = [
  { key: "dashboard", href: "/admin", label: "Dashboard", icon: <LayoutDashboard className="size-4" /> },
  { key: "blog", href: "/admin/blog", label: "Blog posts", icon: <FileText className="size-4" /> },
  { key: "editor", href: "/admin/blog/editor", label: "Compose", icon: <PencilLine className="size-4" /> },
  { key: "ideas", href: "/admin/blog-ideas", label: "Ideas", icon: <Lightbulb className="size-4" /> },
  { key: "projects", href: "/admin/projects", label: "Projects", icon: <Briefcase className="size-4" /> },
  { key: "project-editor", href: "/admin/projects/editor", label: "New project", icon: <PlusCircle className="size-4" /> },
  { key: "showcases", href: "/admin/showcases", label: "Showcases", icon: <Briefcase className="size-4" /> },
  { key: "showcase-editor", href: "/admin/showcases/editor", label: "New showcase", icon: <PlusCircle className="size-4" /> },
  { key: "blog-comments", href: "/admin/blog-comments", label: "Comments", icon: <MessageSquare className="size-4" /> },
  { key: "news-review", href: "/admin/news-review", label: "News review", icon: <Newspaper className="size-4" /> },
  { key: "submitted-links", href: "/admin/news/submitted-links", label: "Submitted links", icon: <LinkIcon className="size-4" /> },
  { key: "news", href: "/admin/news-sources", label: "News sources", icon: <Rss className="size-4" /> },
];

function BrandMark() {
  return (
    <div className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground" aria-hidden>
      <span className="font-(family-name:--font-gt-super) text-base leading-none">A</span>
    </div>
  );
}

function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      aria-pressed={isDark}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      suppressHydrationWarning
      className={cn(
        "inline-flex h-[calc(var(--spacing)*8)] items-center gap-1 rounded-md border border-border px-2.5 text-xs font-medium text-muted-foreground transition-colors",
        "hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
      )}
    >
      {isDark ? <Sun className="size-3" aria-hidden /> : <Moon className="size-3" aria-hidden />}
      <span suppressHydrationWarning>{isDark ? "Light" : "Dark"}</span>
    </button>
  );
}

function NavLink({ active, href, icon, label }: { active: boolean; href: string; icon: ReactNode; label: string }) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50",
        active
          ? "bg-accent text-foreground"
          : "text-muted-foreground hover:bg-muted/60 hover:text-foreground"
      )}
    >
      <span className={cn("flex size-4 shrink-0 items-center justify-center", active && "text-brand")}>{icon}</span>
      {label}
    </Link>
  );
}

export function AdminCmsShell({ active, children }: Props) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <div className="flex min-h-dvh flex-col bg-background lg:flex-row">
      <div className="flex items-center justify-between border-b border-border bg-card px-4 py-3 lg:hidden">
        <div className="flex items-center gap-2.5">
          <BrandMark />
          <div>
            <p className="text-[10px] font-medium leading-none text-muted-foreground">Admin</p>
            <p className="mt-0.5 text-sm font-medium leading-none">Control room</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Link
            className="inline-flex h-[calc(var(--spacing)*8)] items-center gap-1 rounded-md border border-border px-2.5 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
            href="/"
            target="_blank"
            rel="noopener noreferrer"
          >
            Site
            <ExternalLink className="size-3" aria-hidden />
          </Link>
        </div>
      </div>

      <aside className="hidden w-52 shrink-0 flex-col border-r border-border bg-card lg:flex">
        <div className="flex items-center gap-2.5 border-b border-border px-4 py-3.5">
          <BrandMark />
          <div className="min-w-0">
            <p className="text-[10px] font-medium leading-none text-muted-foreground">Admin</p>
            <p className={cn(adminDisplayTitleClass, "mt-0.5 truncate text-base leading-tight")}>Control room</p>
          </div>
        </div>

        <nav aria-label="Admin navigation" className="flex flex-1 flex-col gap-0.5 p-2">
          {navItems.map((item) => (
            <NavLink key={item.key} active={active === item.key} href={item.href} icon={item.icon} label={item.label} />
          ))}
        </nav>

        <div className="flex items-center justify-between gap-2 border-t border-border px-4 py-2.5 text-[11px] text-muted-foreground">
          <span>AI Lab Portal</span>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Link className="font-medium hover:text-foreground" href="/" target="_blank" rel="noopener noreferrer">
              Site
            </Link>
          </div>
        </div>
      </aside>

      <main
        className={cn(
          "min-w-0 flex-1 px-4 py-4 sm:px-5 sm:py-5",
          !prefersReducedMotion && "animate-in fade-in duration-200"
        )}
      >
        {children}
      </main>
    </div>
  );
}
