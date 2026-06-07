"use client";

import { useState } from "react";
import { ChevronDown, CheckCircle2 } from "lucide-react";

import { cn } from "@/lib/utils";

type StepShellState = "active" | "done" | "upcoming" | "blocked";

type Props = {
  stepNumber: number;
  title: string;
  sectionId: string;
  state: StepShellState;
  summary?: string;
  lockedMessage?: string;
  headerActions?: React.ReactNode;
  children: React.ReactNode;
};

export function PipelineStepShell({
  stepNumber,
  title,
  sectionId,
  state,
  summary,
  lockedMessage,
  headerActions,
  children,
}: Props) {
  const [doneExpanded, setDoneExpanded] = useState(false);
  const isOpen = state === "active" || (state === "done" && doneExpanded);

  return (
    <section
      id={sectionId}
      className={cn(
        "min-w-0 scroll-mt-24 rounded-[var(--radius-admin-md)] border transition-colors",
        state === "active"
          ? "border-brand/30 bg-card shadow-[0_1px_3px_0_rgba(0,0,0,0.05)]"
          : "border-border/60 bg-card/80",
        state === "upcoming" && "opacity-70",
      )}
    >
      <div className="flex items-start justify-between gap-3 border-b border-border/60 px-4 py-3 sm:px-5">
        <div className="flex min-w-0 items-start gap-3">
          <span
            className={cn(
              "flex size-7 shrink-0 items-center justify-center rounded-lg text-xs font-bold",
              state === "active"
                ? "bg-brand text-white"
                : state === "done"
                  ? "bg-brand/10 text-brand"
                  : "bg-muted text-muted-foreground",
            )}
          >
            {state === "done" ? <CheckCircle2 className="size-3.5" aria-hidden /> : stepNumber}
          </span>
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-foreground">{title}</h2>
            {state === "done" && summary ? (
              <p className="mt-0.5 truncate text-xs text-muted-foreground">{summary}</p>
            ) : null}
            {state === "upcoming" && lockedMessage ? (
              <p className="mt-0.5 text-xs text-muted-foreground">{lockedMessage}</p>
            ) : null}
          </div>
        </div>

        <div className="flex min-w-0 items-center gap-2">
          {state === "active" && headerActions ? headerActions : null}
          {state === "done" ? (
            <button
              type="button"
              className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-muted/50 hover:text-foreground"
              aria-expanded={isOpen}
              onClick={() => setDoneExpanded((v) => !v)}
            >
              {isOpen ? "Hide" : "Show"}
              <ChevronDown
                className={cn("size-3.5 transition-transform", isOpen && "rotate-180")}
                aria-hidden
              />
            </button>
          ) : null}
        </div>
      </div>

      {isOpen ? <div className="px-4 py-4 sm:px-5 sm:py-5">{children}</div> : null}
    </section>
  );
}

export function stepShellState(
  stepId: string,
  activeId: string,
  idea: { status: string; published_blog_post_id: string | null },
): StepShellState {
  const order = [
    "idea",
    "outline",
    "draft",
    "review",
    "marketing",
    "seo",
    "claims",
    "publish",
  ];
  const idx = order.indexOf(stepId);
  const activeIdx = order.indexOf(activeId);

  if (stepId === "idea" && idea.status === "rejected") {
    return idx === activeIdx ? "active" : "upcoming";
  }
  if (idx < activeIdx) return "done";
  if (idx === activeIdx) return "active";
  return "upcoming";
}
