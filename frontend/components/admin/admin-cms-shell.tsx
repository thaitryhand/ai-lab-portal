"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSyncExternalStore, type ReactNode } from "react";

import { motion } from "framer-motion";
import {
  Activity,
  BarChart3,
  Briefcase,
  CalendarDays,
  ExternalLink,
  FileText,
  LayoutDashboard,
  Lightbulb,
  Link as LinkIcon,
  MessageSquare,
  Moon,
  Newspaper,
  Rss,
  Sun,
} from "lucide-react";
import { useTheme } from "next-themes";

import { BrandMark } from "@/components/brand/brand-mark";
import { cn } from "@/lib/utils";

type NavKey =
  | "dashboard"
  | "observability"
  | "seo"
  | "calendar"
  | "blog"
  | "projects"
  | "showcases"
  | "ideas"
  | "news"
  | "news-review"
  | "submitted-links"
  | "analytics"
  | "blog-comments";

type Props = { children: ReactNode };

/* ── Active nav key from pathname ── */

function useActiveNavKey(): NavKey {
  const pathname = usePathname();
  if (pathname.startsWith("/admin/login")) return "dashboard";
  if (pathname.startsWith("/admin/blog-ideas")) return "ideas";
  if (pathname.startsWith("/admin/analytics")) return "analytics";
  if (pathname.startsWith("/admin/blog-analytics")) return "dashboard";
  if (pathname.startsWith("/admin/blog-comments")) return "blog-comments";
  if (pathname.startsWith("/admin/blog")) return "blog";
  if (pathname.startsWith("/admin/projects")) return "projects";
  if (pathname.startsWith("/admin/showcases")) return "showcases";
  if (pathname.startsWith("/admin/ai-observability")) return "observability";
  if (pathname.startsWith("/admin/seo-analytics")) return "seo";
  if (pathname.startsWith("/admin/content-calendar")) return "calendar";
  if (pathname.startsWith("/admin/news-review")) return "news-review";
  if (pathname.startsWith("/admin/news-sources")) return "news";
  if (pathname.startsWith("/admin/news")) return "submitted-links";
  return "dashboard";
}

/* ── Navigation groups ── */

type NavGroup = {
  label: string;
  items: Array<{ key: NavKey; href: string; label: string; icon: ReactNode }>;
};

const navGroups: NavGroup[] = [
  {
    label: "Overview",
    items: [
      { key: "dashboard", href: "/admin", label: "Dashboard", icon: <LayoutDashboard className="size-4" /> },
      { key: "observability", href: "/admin/ai-observability", label: "Observability", icon: <Activity className="size-4" /> },
      { key: "analytics", href: "/admin/analytics", label: "Analytics", icon: <BarChart3 className="size-4" /> },
      { key: "seo", href: "/admin/seo-analytics", label: "SEO", icon: <BarChart3 className="size-4" /> },
      { key: "calendar", href: "/admin/content-calendar", label: "Calendar", icon: <CalendarDays className="size-4" /> },
    ],
  },
  {
    label: "Content",
    items: [
      { key: "blog", href: "/admin/blog", label: "Blog posts", icon: <FileText className="size-4" /> },
      { key: "ideas", href: "/admin/blog-ideas", label: "Ideas", icon: <Lightbulb className="size-4" /> },
      { key: "blog-comments", href: "/admin/blog-comments", label: "Comments", icon: <MessageSquare className="size-4" /> },
    ],
  },
  {
    label: "Projects & Showcases",
    items: [
      { key: "projects", href: "/admin/projects", label: "Projects", icon: <Briefcase className="size-4" /> },
      { key: "showcases", href: "/admin/showcases", label: "Showcases", icon: <Briefcase className="size-4" /> },
    ],
  },
  {
    label: "AI News",
    items: [
      { key: "news-review", href: "/admin/news-review", label: "News review", icon: <Newspaper className="size-4" /> },
      { key: "submitted-links", href: "/admin/news/submitted-links", label: "Submitted links", icon: <LinkIcon className="size-4" /> },
      { key: "news", href: "/admin/news-sources", label: "News sources", icon: <Rss className="size-4" /> },
    ],
  },
];

/* ── Theme toggle ── */

function ThemeToggle({ compact }: { compact?: boolean }) {
  const { resolvedTheme, setTheme } = useTheme();

  const isClient = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );

  if (!isClient) {
    return (
      <button
        type="button"
        aria-label="Toggle theme"
        suppressHydrationWarning
        className={cn(
          "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-all duration-200",
          "border-border/50 text-muted-foreground/60 hover:border-border/70 hover:text-foreground",
          "active:scale-[0.97]",
          compact ? "h-7 text-[11px]" : "h-8 text-xs",
        )}
      >
        <Sun className="size-3" aria-hidden />
        <span>Light</span>
      </button>
    );
  }

  const isDark = resolvedTheme === "dark";

  return (
    <button
      type="button"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      aria-pressed={isDark}
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition-all duration-200",
        "border-border/50 text-muted-foreground/60 hover:border-border/70 hover:text-foreground",
        "active:scale-[0.97]",
        compact ? "h-7 text-[11px]" : "h-8 text-xs",
      )}
    >
      {isDark ? <Sun className="size-3" aria-hidden /> : <Moon className="size-3" aria-hidden />}
      <span className="hidden sm:inline">
        {isDark ? "Light" : "Dark"}
      </span>
    </button>
  );
}

/* ── Nav link ── */

function NavLink({
  active,
  href,
  icon,
  label,
}: {
  active: boolean;
  href: string;
  icon: ReactNode;
  label: string;
}) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={cn(
        "group relative flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/40 focus-visible:ring-offset-2 focus-visible:ring-offset-sidebar",
        active
          ? "bg-brand/10 text-brand"
          : "text-sidebar-foreground/60 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground/90"
      )}
    >
      {/* Active indicator bar */}
      {active && (
        <motion.span
          layoutId="nav-indicator"
          className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-brand shadow-[0_0_8px_rgba(80,179,58,0.4)]"
          transition={{ type: "spring", stiffness: 400, damping: 30 }}
        />
      )}

      {/* Icon */}
      <span
        className={cn(
          "flex size-4 shrink-0 items-center justify-center transition-colors",
          active && "text-brand"
        )}
      >
        {icon}
      </span>

      {/* Label */}
      <span>{label}</span>
    </Link>
  );
}

/* ══════════════════════════════════════════
   AdminCmsShell
   ══════════════════════════════════════════ */

export function AdminCmsShell({ children }: Props) {
  const active = useActiveNavKey();

  return (
    <div className="flex min-h-dvh flex-col bg-background lg:flex-row">
      {/* ── Mobile header ── */}
      <div className="flex items-center justify-between border-b border-border/50 bg-sidebar px-4 py-3 lg:hidden">
        <div className="flex items-center gap-2.5">
          <BrandMark />
          <div className="h-4 w-px bg-sidebar-border" aria-hidden />
          <p className="text-sm font-semibold text-sidebar-foreground">AI Lab</p>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle compact />
          <Link
            className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-sidebar-border px-2.5 text-xs font-medium text-sidebar-foreground/60 transition-all duration-200 hover:border-sidebar-border/80 hover:text-sidebar-foreground/90 active:scale-[0.97]"
            href="/"
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink className="size-3" aria-hidden />
          </Link>
        </div>
      </div>

      {/* ── Desktop sidebar ── */}
      <aside className="hidden w-56 shrink-0 flex-col border-r border-sidebar-border bg-sidebar shadow-[2px_0_12px_rgba(0,0,0,0.06)] lg:sticky lg:top-0 lg:flex lg:h-dvh lg:self-start">
        {/* Brand accent line */}
        <div className="h-[3px] w-full bg-gradient-to-r from-brand/0 via-brand to-brand/0" />

        {/* Brand header */}
        <Link
          href="/"
          className="group flex items-center gap-2.5 border-b border-sidebar-border px-4 py-4 transition-colors hover:bg-sidebar-accent/30"
        >
          <div className="relative">
            <BrandMark />
            <span className="absolute -right-0.5 -top-0.5 size-2 rounded-full bg-brand shadow-[0_0_6px_rgba(80,179,58,0.5)]" aria-hidden />
          </div>
          <div>
            <p className="text-sm font-semibold text-sidebar-foreground">AI Lab</p>
            <p className="text-[10px] text-sidebar-foreground/40">Control panel</p>
          </div>
        </Link>

        {/* Navigation */}
        <nav
          aria-label="Admin navigation"
          className="flex min-h-0 flex-1 flex-col gap-0.5 overflow-y-auto p-3"
        >
          {navGroups.map((group) => (
            <div key={group.label} className="flex flex-col">
              <span className="px-3 pb-1.5 pt-3.5 text-[10px] font-semibold uppercase tracking-[0.1em] text-sidebar-foreground/30 select-none">
                {group.label}
              </span>
              {group.items.map((item) => (
                <NavLink
                  key={item.key}
                  active={active === item.key}
                  href={item.href}
                  icon={item.icon}
                  label={item.label}
                />
              ))}
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t border-sidebar-border px-3 py-3">
          <div className="flex items-center justify-between gap-1">
            <Link
              className="inline-flex h-8 items-center gap-1.5 rounded-lg px-2.5 text-[11px] font-medium text-sidebar-foreground/50 transition-colors hover:bg-sidebar-accent/50 hover:text-sidebar-foreground/80"
              href="/"
              target="_blank"
              rel="noopener noreferrer"
            >
              <ExternalLink className="size-3" aria-hidden />
              View site
            </Link>
            <ThemeToggle compact />
          </div>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main className="min-w-0 flex-1 px-5 py-6 sm:px-8 sm:py-8 lg:px-10">
        {children}
      </main>
    </div>
  );
}
