import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { ArrowUpRight, Lightbulb, PencilLine } from "lucide-react";

import { cn } from "@/lib/utils";

export type AdminDashboardStat = {
  href: string;
  hint: string;
  icon: LucideIcon;
  label: string;
  value: number;
};

/* ── Per-stat accent palette ── */
const statAccents: Record<
  string,
  { bg: string; iconBg: string; ring: string }
> = {
  "Blog posts": {
    bg: "bg-emerald-50 dark:bg-emerald-950/20",
    iconBg: "bg-emerald-600 dark:bg-emerald-500",
    ring: "ring-emerald-200/50 dark:ring-emerald-800/30",
  },
  "Blog ideas": {
    bg: "bg-amber-50 dark:bg-amber-950/20",
    iconBg: "bg-amber-600 dark:bg-amber-500",
    ring: "ring-amber-200/50 dark:ring-amber-800/30",
  },
  Showcases: {
    bg: "bg-violet-50 dark:bg-violet-950/20",
    iconBg: "bg-violet-600 dark:bg-violet-500",
    ring: "ring-violet-200/50 dark:ring-violet-800/30",
  },
  "AI News": {
    bg: "bg-sky-50 dark:bg-sky-950/20",
    iconBg: "bg-sky-600 dark:bg-sky-500",
    ring: "ring-sky-200/50 dark:ring-sky-800/30",
  },
};

type Props = { stats: AdminDashboardStat[] };

export function AdminDashboardStatGrid({ stats }: Props) {
  return (
    <section
      aria-labelledby="stats-heading"
      className="grid gap-5 lg:grid-cols-[11rem_minmax(0,1fr)]"
    >
      {/* Side label */}
      <div className="flex flex-col justify-center rounded-[var(--radius-admin-md)] border border-border/60 bg-card px-5 py-5 shadow-[0_1px_3px_rgba(0,0,0,0.03)]">
        <h2
          id="stats-heading"
          className="text-sm font-semibold text-foreground"
        >
          At a glance
        </h2>
        <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
          Publishing inventory by surface.
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          const accent = statAccents[stat.label] ?? {
            bg: "bg-muted/30",
            iconBg: "bg-muted-foreground",
            ring: "ring-border/30",
          };

          return (
            <Link
              key={stat.label}
              className={cn(
                "group relative overflow-hidden rounded-[var(--radius-admin-md)] border border-border/60 p-5 shadow-[0_1px_3px_rgba(0,0,0,0.03)] transition-all duration-200",
                accent.bg,
                "hover:-translate-y-[1px] hover:shadow-[0_4px_14px_rgba(0,0,0,0.06)]",
                "focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:ring-offset-2",
              )}
              href={stat.href}
            >
              {/* Top row: icon + arrow */}
              <div className="flex items-start justify-between gap-2">
                <span
                  className={cn(
                    "flex size-9 items-center justify-center rounded-[var(--radius-admin-sm)] text-white shadow-[inset_0_1px_0_rgba(255,255,255,0.2)] ring-1",
                    accent.iconBg,
                    accent.ring,
                  )}
                >
                  <Icon className="size-[18px]" aria-hidden />
                </span>
                <ArrowUpRight
                  className="size-3.5 text-muted-foreground/25 transition-colors group-hover:text-muted-foreground/50"
                  aria-hidden
                />
              </div>

              {/* Number + label */}
              <div className="mt-4">
                <p className="text-xs font-medium text-muted-foreground/80">
                  {stat.label}
                </p>
                <p className="mt-1 font-(family-name:--font-sohne) text-[2rem] font-semibold leading-none tracking-tight text-foreground tabular-nums">
                  {stat.value}
                </p>
                <p className="mt-2 text-xs text-muted-foreground">
                  {stat.hint}
                </p>
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}

export function AdminQuickActionPanel() {
  return (
    <div className="grid grid-cols-2 gap-2">
      <Link
        className="group flex min-h-[4.25rem] flex-col justify-between rounded-[var(--radius-admin-sm)] bg-primary p-3.5 text-primary-foreground transition-all duration-200 hover:bg-primary/90 hover:shadow-[0_2px_8px_rgba(0,0,0,0.12)] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:ring-offset-2 active:scale-[0.98]"
        href="/admin/blog/editor"
      >
        <PencilLine className="size-4" aria-hidden />
        <span className="text-sm font-medium leading-tight">New draft</span>
      </Link>
      <Link
        className="group flex min-h-[4.25rem] flex-col justify-between rounded-[var(--radius-admin-sm)] border border-border/60 bg-card p-3.5 text-foreground transition-all duration-200 hover:border-border hover:bg-muted/30 hover:shadow-[0_2px_6px_rgba(0,0,0,0.04)] focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:ring-offset-2 active:scale-[0.98]"
        href="/admin/blog-ideas/new"
      >
        <Lightbulb className="size-4 text-brand" aria-hidden />
        <span className="text-sm font-medium leading-tight">New idea</span>
      </Link>
    </div>
  );
}
