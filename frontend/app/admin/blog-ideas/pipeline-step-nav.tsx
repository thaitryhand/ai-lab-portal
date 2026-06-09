"use client";

import Link from "next/link";
import { CheckCircle2, Circle, Loader2, Lock } from "lucide-react";

import { cn } from "@/lib/utils";

import type { PipelineNextAction, PipelineStageId } from "./lib/pipeline-next-action";

export type PipelineStepDef = {
  id: PipelineStageId;
  label: string;
  anchor: string;
};

export const PIPELINE_STEPS: PipelineStepDef[] = [
  { id: "idea", label: "Idea", anchor: "pipeline-section-idea" },
  { id: "collect", label: "Context", anchor: "pipeline-section-collect" },
  { id: "outline", label: "Outline", anchor: "pipeline-section-outline" },
  { id: "draft", label: "Draft", anchor: "pipeline-section-draft" },
  { id: "review", label: "Review", anchor: "pipeline-section-review" },
  { id: "marketing", label: "Marketing", anchor: "pipeline-section-marketing" },
  { id: "claims", label: "Claims", anchor: "pipeline-section-claims" },
  { id: "publish", label: "Publish", anchor: "pipeline-section-publish" },
];

type StepVisualState = "done" | "active" | "upcoming" | "blocked";

function stepVisualState(
  stepId: PipelineStageId,
  activeId: PipelineStageId,
  idea: {
    status: string;
    knowledge_context_status: string | null;
    outline_status: string | null;
    draft_status: string | null;
    technical_review_status: string | null;
    marketing_status: string | null;
    seo_audit_status: string | null;
    published_blog_post_id: string | null;
  },
): StepVisualState {
  const order = PIPELINE_STEPS.map((s) => s.id);
  const stepIndex = order.indexOf(stepId);
  const activeIndex = order.indexOf(activeId);

  if (stepId === "idea") {
    if (idea.status === "rejected") return "blocked";
    if (idea.status === "approved") return stepIndex < activeIndex ? "done" : stepIndex === activeIndex ? "active" : "upcoming";
    return stepIndex === activeIndex ? "active" : "upcoming";
  }

  if (stepIndex < activeIndex) return "done";
  if (stepIndex === activeIndex) return "active";
  return "upcoming";
}

type Props = {
  idea: {
    status: string;
    knowledge_context_status: string | null;
    outline_status: string | null;
    draft_status: string | null;
    technical_review_status: string | null;
    marketing_status: string | null;
    seo_audit_status: string | null;
    published_blog_post_id: string | null;
  };
  nextAction: PipelineNextAction;
};

export function PipelineStepNav({ idea, nextAction }: Props) {
  const activeId = nextAction.stageId;

  return (
    <nav
      aria-label="Blog pipeline steps"
      className="rounded-[var(--radius-admin-md)] border border-border/70 bg-card p-3 shadow-[0_1px_3px_0_rgba(0,0,0,0.04)] lg:sticky lg:top-20"
    >
      <p className="mb-3 px-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
        Pipeline
      </p>
      <ol className="grid gap-0.5">
        {PIPELINE_STEPS.map((step, index) => {
          const state = stepVisualState(step.id, activeId, idea);
          const isActive = state === "active";

          return (
            <li key={step.id}>
              <Link
                href={`#${step.anchor}`}
                className={cn(
                  "flex items-start gap-2.5 rounded-lg px-2 py-2 text-left transition-colors",
                  isActive
                    ? "bg-brand/8 text-foreground ring-1 ring-brand/20"
                    : "text-muted-foreground hover:bg-muted/40 hover:text-foreground",
                )}
              >
                <StepIcon index={index} state={state} processing={isActive && nextAction.kind === "processing"} />
                <span className="min-w-0 flex-1">
                  <span
                    className={cn(
                      "block text-sm font-medium leading-tight",
                      isActive && "text-foreground",
                    )}
                  >
                    {step.label}
                  </span>
                  {isActive ? (
                    <span className="mt-0.5 block text-xs leading-snug text-muted-foreground">
                      {nextAction.title}
                    </span>
                  ) : null}
                </span>
              </Link>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

function StepIcon({
  index,
  state,
  processing,
}: {
  index: number;
  state: StepVisualState;
  processing: boolean;
}) {
  if (processing) {
    return <Loader2 className="mt-0.5 size-4 shrink-0 animate-spin text-brand" aria-hidden />;
  }
  if (state === "done") {
    return <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-brand" aria-hidden />;
  }
  if (state === "blocked") {
    return <Lock className="mt-0.5 size-4 shrink-0 text-red-400" aria-hidden />;
  }
  if (state === "active") {
    return (
      <span className="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-brand text-[10px] font-bold text-white">
        {index + 1}
      </span>
    );
  }
  return <Circle className="mt-0.5 size-4 shrink-0 text-muted-foreground/40" aria-hidden />;
}
