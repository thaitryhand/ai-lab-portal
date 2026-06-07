"use client";

import React from "react";
import Link from "next/link";
import { useFormStatus } from "react-dom";

import {
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  AlertCircle,
  Sparkles,
  FileText,
  Search,
  Tag,
  MessageSquare,
  Send,
  ExternalLink,
  Loader2,
  Activity,
} from "lucide-react";

import { AdminBackLink } from "@/components/admin/admin-back-link";
import {
  adminPageStackClass,
  adminPageTitleClass,
} from "@/components/admin/admin-ui";
import { buttonVariants } from "@/components/ui/button-variants";
import { cn } from "@/lib/utils";

import { ClaimReviewPanel } from "./claim-review-panel";
import { claimsBlockPublish } from "./lib/claim-publish-gate";
import { approveButtonLabel } from "./lib/pipeline-next-stage";
import { getPipelineNextAction } from "./lib/pipeline-next-action";
import { PipelineStepNav } from "./pipeline-step-nav";
import { PipelineStepShell, stepShellState } from "./pipeline-step-shell";
import { StageStreamButton } from "@/components/admin/stage-stream-button";
import { ReadabilityBadge } from "@/components/admin/readability-badge";
import { InternalLinks } from "@/components/admin/internal-links";
import { ScheduleButton } from "@/components/admin/schedule-button";
import { ThumbnailButton } from "@/components/admin/thumbnail-button";

// ─── Types ───────────────────────────────────────────────────────

type OutlineSection = {
  section: string;
  points: string[];
};

export type BlogIdeaDetail = {
  id: string;
  title: string;
  angle: string;
  target_reader: string;
  article_goal: string;
  positioning_notes: string[];
  source: "manual" | "ai_generated";
  source_project_context: Record<string, string> | null;
  status: "pending" | "approved" | "rejected";
  reviewed_by: string | null;
  reviewed_at: string | null;
  feedback: string | null;
  outline_sections: OutlineSection[];
  outline_status: string | null;
  draft_markdown: string | null;
  draft_status: string | null;
  technical_review: {
    overall_risk: string;
    issues: Array<{
      severity: string;
      type?: string;
      issue_type: string;
      text: string;
      reason: string;
      suggestion: string;
    }>;
    approval_recommendation: string;
  } | null;
  technical_review_status: string | null;
  marketing_metadata: {
    seo_title: string;
    meta_description: string;
    canonical_url: string;
    social_headline: string;
    social_description: string;
    cta_text: string;
    tags: string[];
  } | null;
  marketing_status: string | null;
  published_blog_post_id: string | null;
  scheduled_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AiRunItem = {
  id: string;
  prompt_name: string;
  prompt_version: string;
  status: "completed" | "failed";
  provider: string;
  model: string;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  latency_ms: number | null;
  error_message: string | null;
  trace_id: string | null;
  created_at: string;
};

export type BlogClaimItem = {
  id: string;
  blog_idea_id: string;
  claim_text: string;
  claim_type: string;
  status: "pending" | "supported" | "unsupported" | "waived";
  evidence_source_type: string | null;
  evidence_reference: string | null;
};

// ─── Helpers ──────────────────────────────────────────────────────

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const statusColors: Record<string, string> = {
  approved:
    "text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950/30",
  rejected:
    "text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-950/30",
  pending:
    "text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950/30",
};

const severityConfig = {
  high: {
    icon: AlertCircle,
    className:
      "border-red-200 bg-red-50/70 dark:border-red-900 dark:bg-red-950/15",
    badge: "text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-950/40",
  },
  medium: {
    icon: AlertTriangle,
    className:
      "border-amber-200 bg-amber-50/70 dark:border-amber-900 dark:bg-amber-950/15",
    badge:
      "text-amber-600 bg-amber-100 dark:text-amber-400 dark:bg-amber-950/40",
  },
  low: {
    icon: MessageSquare,
    className:
      "border-sky-200 bg-sky-50/70 dark:border-sky-900 dark:bg-sky-950/15",
    badge:
      "text-sky-600 bg-sky-100 dark:text-sky-400 dark:bg-sky-950/40",
  },
};

// ─── Actions Props ───────────────────────────────────────────────

type Actions = {
  approveIdea: (formData: FormData) => Promise<void>;
  rejectIdea: (formData: FormData) => Promise<void>;
  generateOutline: (formData: FormData) => Promise<void>;
  approveOutline: (formData: FormData) => Promise<void>;
  rejectOutline: (formData: FormData) => Promise<void>;
  generateDraft: (formData: FormData) => Promise<void>;
  approveDraft: (formData: FormData) => Promise<void>;
  rejectDraft: (formData: FormData) => Promise<void>;
  reviewTechnical: (formData: FormData) => Promise<void>;
  approveReview: (formData: FormData) => Promise<void>;
  rejectReview: (formData: FormData) => Promise<void>;
  generateMarketing: (formData: FormData) => Promise<void>;
  approveMarketing: (formData: FormData) => Promise<void>;
  rejectMarketing: (formData: FormData) => Promise<void>;
  publishToBlog: (formData: FormData) => Promise<void>;
  extractClaims: (formData: FormData) => Promise<void>;
  updateClaim: (formData: FormData) => Promise<void>;
  waiveAllClaims: (formData: FormData) => Promise<void>;
};

// ─── Main Component ──────────────────────────────────────────────

type OperationalStatus = {
  message?: string;
  opStage?: string;
  opStatus?: string;
  taskId?: string;
  blogPostId?: string;
  blogSlug?: string;
};

type Props = {
  idea: BlogIdeaDetail;
  claims?: BlogClaimItem[];
  aiRuns?: AiRunItem[];
  operationalStatus?: OperationalStatus;
  actions: Actions;
};

export function BlogIdeaDetailView({ idea, claims = [], aiRuns = [], operationalStatus, actions }: Props) {
  const nextAction = getPipelineNextAction(idea, claims.length, operationalStatus);
  const showOpBanner =
    Boolean(operationalStatus?.message) && operationalStatus?.opStatus !== "queued";

  const ideaStepState = stepShellState("idea", nextAction.stageId, idea);
  const outlineStepState = stepShellState("outline", nextAction.stageId, idea);
  const draftStepState = stepShellState("draft", nextAction.stageId, idea);
  const reviewStepState = stepShellState("review", nextAction.stageId, idea);
  const marketingStepState = stepShellState("marketing", nextAction.stageId, idea);
  const claimsStepState = stepShellState("claims", nextAction.stageId, idea);
  const publishStepState = stepShellState("publish", nextAction.stageId, idea);

  return (
    <div className={adminPageStackClass}>
      <AdminBackLink href="/admin/blog-ideas">Back to ideas</AdminBackLink>

      <header className="flex flex-col gap-2 border-b border-border/60 pb-5">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium",
              statusColors[idea.status],
            )}
          >
            {idea.status === "approved" ? (
              <CheckCircle className="size-3" />
            ) : idea.status === "rejected" ? (
              <XCircle className="size-3" />
            ) : (
              <Clock className="size-3" />
            )}
            {idea.status}
          </span>
          <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
            {idea.source === "ai_generated" ? (
              <Sparkles className="size-3" />
            ) : (
              <FileText className="size-3" />
            )}
            {idea.source === "ai_generated" ? "AI-generated" : "Manual"}
          </span>
          <span className="text-[11px] text-muted-foreground">
            Updated {formatDate(idea.updated_at)}
          </span>
        </div>
        <h1 className={adminPageTitleClass}>{idea.title}</h1>
        {nextAction.kind !== "done" && nextAction.kind !== "processing" ? (
          <p className="max-w-2xl text-sm text-muted-foreground">{nextAction.description}</p>
        ) : null}
      </header>

      {showOpBanner ? <OperationalStatusBanner status={operationalStatus!} /> : null}

      <div className="grid items-start gap-6 lg:grid-cols-[13.5rem_minmax(0,1fr)] xl:grid-cols-[15rem_minmax(0,1fr)]">
        <PipelineStepNav idea={idea} nextAction={nextAction} />

        <div className="grid gap-4 min-w-0">
          <PipelineStepShell
            stepNumber={1}
            title="Idea"
            sectionId="pipeline-section-idea"
            state={ideaStepState}
            summary={idea.angle}
            lockedMessage="Idea was rejected."
            headerActions={
              idea.status === "pending" ? (
                <ActionButtons
                  approveAction={actions.approveIdea}
                  rejectAction={actions.rejectIdea}
                  ideaId={idea.id}
                  approveLabel={approveButtonLabel("idea")}
                  rejectLabel="Reject"
                />
              ) : undefined
            }
          >
            <div className="grid gap-5 sm:grid-cols-3">
              <MetaField label="Angle" value={idea.angle} />
              <MetaField label="Target reader" value={idea.target_reader} />
              <MetaField label="Article goal" value={idea.article_goal} />
            </div>
            {idea.positioning_notes.length > 0 ? (
              <div className="mt-5 border-t border-border/60 pt-4">
                <p className="text-xs font-medium text-muted-foreground">Positioning notes</p>
                <ul className="mt-2 space-y-1.5">
                  {idea.positioning_notes.map((note, i) => (
                    <li
                      key={`note-${note.slice(0, 24)}-${i}`}
                      className="text-sm leading-snug text-foreground [overflow-wrap:anywhere]"
                    >
                      {note}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            {idea.feedback ? (
              <p className="mt-4 text-sm italic text-muted-foreground [overflow-wrap:anywhere]">{idea.feedback}</p>
            ) : null}
          </PipelineStepShell>

          <PipelineStepShell
            stepNumber={2}
            title="Outline"
            sectionId="pipeline-section-outline"
            state={outlineStepState}
            summary={
              idea.outline_sections.length > 0
                ? `${idea.outline_sections.length} sections · ${idea.outline_status ?? "draft"}`
                : undefined
            }
            lockedMessage="Approve the idea to generate an outline."
            headerActions={
              idea.outline_status === "pending" ? (
                <ActionButtons
                  approveAction={actions.approveOutline}
                  rejectAction={actions.rejectOutline}
                  ideaId={idea.id}
                  approveLabel={approveButtonLabel("outline")}
                  rejectLabel="Reject"
                />
              ) : undefined
            }
          >
        {idea.outline_sections.length === 0 ? (
          <>
          <EmptyState
            message={
              idea.status === "approved"
                ? "No outline generated yet. Generation requires the worker and OpenAI key to be configured."
                : "Approve the idea first to enable outline generation."
            }
            action={
              idea.status === "approved" && !idea.outline_status
                ? {
                    label: "Generate outline",
                    icon: Sparkles,
                    actionName: actions.generateOutline,
                    ideaId: idea.id,
                  }
                : undefined
            }
          />
          {idea.status === "approved" && !idea.outline_status ? (
            <StageStreamButton stage="outline" ideaId={idea.id} label="Stream outline" />
          ) : null}
          </>
        ) : (
          <div className="grid gap-4">
            {idea.outline_status === "rejected" && idea.status === "approved" ? (
              <RegenerateAction
                actionName={actions.generateOutline}
                ideaId={idea.id}
                label="Regenerate outline"
              />
            ) : null}
            <div className="grid gap-4 sm:grid-cols-2">
              {idea.outline_sections.map((section, i) => (
                <div key={section.section} className="rounded-lg border border-border/70 bg-muted/30 p-4">
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-foreground">
                    <span className="flex size-5 items-center justify-center rounded-md bg-brand/10 text-[10px] font-bold text-brand">
                      {i + 1}
                    </span>
                    {section.section}
                  </h3>
                  <ul className="mt-3 space-y-1.5">
                    {section.points.map((point, j) => (
                      <li
                        key={`${section.section}-point-${j}`}
                        className="text-sm leading-snug text-muted-foreground [overflow-wrap:anywhere]"
                      >
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}
          </PipelineStepShell>

          <PipelineStepShell
            stepNumber={3}
            title="Draft"
            sectionId="pipeline-section-draft"
            state={draftStepState}
            summary={
              idea.draft_markdown
                ? `${idea.draft_markdown.split(/\s+/).filter(Boolean).length.toLocaleString()} words · ${idea.draft_status ?? "draft"}`
                : undefined
            }
            lockedMessage="Approve the outline to generate a draft."
            headerActions={
              idea.draft_status === "pending" ? (
                <ActionButtons
                  approveAction={actions.approveDraft}
                  rejectAction={actions.rejectDraft}
                  ideaId={idea.id}
                  approveLabel={approveButtonLabel("draft")}
                  rejectLabel="Reject"
                />
              ) : undefined
            }
          >
        {!idea.draft_markdown ? (
          <>
          <EmptyState
            message={
              idea.outline_status === "approved"
                ? "No draft generated yet. Generation requires the worker and OpenAI key to be configured."
                : "Approve the outline first to enable draft generation."
            }
            action={
              idea.outline_status === "approved" && !idea.draft_status
                ? {
                    label: "Generate draft",
                    icon: Sparkles,
                    actionName: actions.generateDraft,
                    ideaId: idea.id,
                  }
                : undefined
            }
          />
          {idea.outline_status === "approved" && !idea.draft_status ? (
            <StageStreamButton stage="draft" ideaId={idea.id} label="Stream draft" />
          ) : null}
          </>
        ) : (
          <div className="grid gap-4">
            {idea.draft_markdown ? (
              <div className="flex items-center gap-3 text-xs text-muted-foreground">
                <span>
                  {idea.draft_markdown.split(/\s+/).filter(Boolean).length.toLocaleString()} words
                </span>
                <ReadabilityBadge text={idea.draft_markdown} />
                <InternalLinks ideaId={idea.id} enabled={!!idea.draft_markdown} />
              </div>
            ) : null}
            {idea.draft_status === "rejected" && idea.outline_status === "approved" ? (
              <RegenerateAction
                actionName={actions.generateDraft}
                ideaId={idea.id}
                label="Regenerate draft"
              />
            ) : null}
            <div className="max-h-[32rem] overflow-y-auto overflow-x-auto rounded-lg border border-border/70 bg-muted/20 p-5">
              {idea.draft_markdown.split("\n").map((line, i) => {
                if (line.startsWith("## ")) {
                  return (
                    <h2 key={i} className="mb-2 mt-5 text-lg font-semibold tracking-[-0.02em] text-foreground first:mt-0">
                      {line.slice(3)}
                    </h2>
                  );
                }
                if (line.startsWith("### ")) {
                  return (
                    <h3 key={i} className="mb-1.5 mt-4 text-base font-semibold text-foreground">
                      {line.slice(4)}
                    </h3>
                  );
                }
                if (line.startsWith("- **")) {
                  const boldEnd = line.indexOf("**", 4);
                  const boldText = line.slice(4, boldEnd);
                  const rest = line.slice(boldEnd + 2);
                  return (
                    <li key={i} className="ml-4 text-sm leading-7 text-muted-foreground">
                      <strong className="text-foreground">{boldText}</strong>
                      {rest}
                    </li>
                  );
                }
                if (line.startsWith("- ")) {
                  return (
                    <li key={i} className="ml-4 text-sm leading-7 text-muted-foreground">
                      {line.slice(2)}
                    </li>
                  );
                }
                if (line.startsWith("**")) {
                  const match = line.match(/\*\*(.+?)\*\*/);
                  if (match) {
                    return (
                      <p key={i} className="text-sm leading-7 text-muted-foreground">
                        <strong className="text-foreground">{match[1]}</strong>
                        {line.slice(match[0].length)}
                      </p>
                    );
                  }
                }
                if (line.trim() === "") {
                  return <div key={i} className="h-3" />;
                }
                return (
                  <p key={i} className="text-sm leading-7 text-muted-foreground">
                    {line}
                  </p>
                );
              })}
            </div>
          </div>
        )}
          </PipelineStepShell>

          <PipelineStepShell
            stepNumber={4}
            title="Technical review"
            sectionId="pipeline-section-review"
            state={reviewStepState}
            summary={
              idea.technical_review
                ? `${idea.technical_review.overall_risk} risk · ${idea.technical_review.issues.length} issues`
                : undefined
            }
            lockedMessage="Approve the draft to run technical review."
            headerActions={
              idea.technical_review_status === "pending" ? (
                <ActionButtons
                  approveAction={actions.approveReview}
                  rejectAction={actions.rejectReview}
                  ideaId={idea.id}
                  approveLabel={approveButtonLabel("review")}
                  rejectLabel="Changes"
                />
              ) : undefined
            }
          >
        {!idea.technical_review ? (
          <>
          <EmptyState
            message={
              idea.draft_status === "approved"
                ? "No technical review yet. Generation requires the worker and OpenAI key to be configured."
                : "Approve the draft first to enable technical review."
            }
            action={
              idea.draft_status === "approved" && !idea.technical_review_status
                ? {
                    label: "Run technical review",
                    icon: Search,
                    actionName: actions.reviewTechnical,
                    ideaId: idea.id,
                  }
                : undefined
            }
          />
          {idea.draft_status === "approved" && !idea.technical_review_status ? (
            <StageStreamButton stage="review" ideaId={idea.id} label="Stream review" />
          ) : null}
          </>
        ) : (
          <div className="grid gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium",
                  idea.technical_review.overall_risk === "low"
                    ? "text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950/30"
                    : idea.technical_review.overall_risk === "medium"
                      ? "text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950/30"
                      : "text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-950/30"
                )}
              >
                <AlertTriangle className="size-3.5" />
                Risk: {idea.technical_review.overall_risk}
              </span>
              {idea.technical_review.approval_recommendation && (
                <span className="text-xs text-muted-foreground">
                  Recommendation: {idea.technical_review.approval_recommendation}
                </span>
              )}
            </div>

            {idea.technical_review_status === "rejected" && idea.draft_status === "approved" ? (
              <RegenerateAction
                actionName={actions.reviewTechnical}
                ideaId={idea.id}
                label="Run review again"
              />
            ) : null}

            {idea.technical_review.issues.length === 0 ? (
              <p className="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
                <CheckCircle className="size-4" />
                No issues found. The draft passes technical review.
              </p>
            ) : (
              <div className="grid gap-3">
                {idea.technical_review.issues.map((issue, i) => {
                  const config =
                    severityConfig[issue.severity as keyof typeof severityConfig] ??
                    severityConfig.low;
                  const SevIcon = config.icon;
                  const issueKey = `${issue.issue_type}-${issue.text.slice(0, 32)}-${i}`;
                  return (
                    <div
                      key={issueKey}
                      className={cn(
                        "rounded-xl border p-4 transition-all hover:shadow-sm",
                        config.className
                      )}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-2">
                          <SevIcon
                            className={cn(
                              "size-4",
                              issue.severity === "high"
                                ? "text-red-500"
                                : issue.severity === "medium"
                                  ? "text-amber-500"
                                  : "text-sky-500"
                            )}
                            aria-hidden
                          />
                          <span
                            className={cn(
                              "inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest",
                              config.badge
                            )}
                          >
                            {issue.severity}
                          </span>
                          <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                            {issue.issue_type.replace(/_/g, " ")}
                          </span>
                        </div>
                      </div>
                      <div className="mt-3 grid gap-2">
                        <p className="text-sm leading-snug text-foreground [overflow-wrap:anywhere]">
                          <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                            Text:
                          </span>{" "}
                          {issue.text}
                        </p>
                        <p className="text-sm leading-snug text-muted-foreground [overflow-wrap:anywhere]">
                          <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                            Issue:
                          </span>{" "}
                          {issue.reason}
                        </p>
                        <p className="text-sm leading-snug italic text-brand [overflow-wrap:anywhere]">
                          <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground not-italic">
                            Suggestion:
                          </span>{" "}
                          {issue.suggestion}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
          </PipelineStepShell>

          <PipelineStepShell
            stepNumber={5}
            title="Marketing"
            sectionId="pipeline-section-marketing"
            state={marketingStepState}
            summary={idea.marketing_metadata?.seo_title}
            lockedMessage="Accept the technical review to generate marketing metadata."
            headerActions={
              idea.marketing_status === "pending" ? (
                <ActionButtons
                  approveAction={actions.approveMarketing}
                  rejectAction={actions.rejectMarketing}
                  ideaId={idea.id}
                  approveLabel={approveButtonLabel("marketing")}
                  rejectLabel="Regenerate"
                />
              ) : undefined
            }
          >
        {!idea.marketing_metadata ? (
          <>
          <EmptyState
            message={
              idea.technical_review_status === "approved"
                ? "No marketing metadata yet. Generation requires the worker and OpenAI key to be configured."
                : "Accept the technical review first to enable marketing generation."
            }
            action={
              idea.technical_review_status === "approved" && !idea.marketing_status
                ? {
                    label: "Generate marketing metadata",
                    icon: Sparkles,
                    actionName: actions.generateMarketing,
                    ideaId: idea.id,
                  }
                : undefined
            }
          />
          {idea.technical_review_status === "approved" && !idea.marketing_status ? (
            <StageStreamButton stage="marketing" ideaId={idea.id} label="Stream marketing" />
          ) : null}
          </>
        ) : (
          <div className="grid gap-5">
            {idea.marketing_status === "rejected" && idea.technical_review_status === "approved" ? (
              <RegenerateAction
                actionName={actions.generateMarketing}
                ideaId={idea.id}
                label="Regenerate marketing"
              />
            ) : null}
            <MarketingField label="SEO Title" value={idea.marketing_metadata.seo_title} />
              <MarketingField
                label="Meta Description"
                value={idea.marketing_metadata.meta_description}
              />
              <MarketingField
                label="Social Headline"
                value={idea.marketing_metadata.social_headline}
              />
              <MarketingField
                label="Social Description"
                value={idea.marketing_metadata.social_description}
              />
              <MarketingField
                label="CTA"
                value={idea.marketing_metadata.cta_text}
              />
              {idea.marketing_metadata.tags &&
                idea.marketing_metadata.tags.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground">
                      Tags
                    </p>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {idea.marketing_metadata.tags.map((tag) => (
                        <span
                          key={tag}
                          className="inline-flex items-center gap-1 rounded-md border border-border bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                        >
                          <Tag className="size-3" />
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
          </div>
        )}
          </PipelineStepShell>

          <PipelineStepShell
            stepNumber={6}
            title="Claims"
            sectionId="pipeline-section-claims"
            state={claimsStepState}
            summary={
              claims.length > 0
                ? `${claims.length} claims · ${claims.filter((c) => c.status !== "pending" && c.status !== "unsupported").length} cleared`
                : undefined
            }
            lockedMessage="Approve marketing metadata before extracting claims."
          >
        {idea.marketing_status !== "approved" ? (
          <EmptyState message="Approve marketing metadata before extracting claims for the evidence ledger." />
        ) : (
          <ClaimReviewPanel
            actions={{
              extractClaims: actions.extractClaims,
              updateClaim: actions.updateClaim,
              waiveAllClaims: actions.waiveAllClaims,
            }}
            claims={claims}
            ideaId={idea.id}
          />
        )}
          </PipelineStepShell>

          <PipelineStepShell
            stepNumber={7}
            title="Publish"
            sectionId="pipeline-section-publish"
            state={publishStepState}
            summary={idea.published_blog_post_id ? "Published to blog" : undefined}
            lockedMessage="Clear claims and approve marketing before publishing."
          >
        {idea.published_blog_post_id ? (
          <div className="flex flex-wrap gap-2">
            <Link
              href={`/admin/blog/${idea.published_blog_post_id}/edit`}
              className={cn(buttonVariants({ variant: "secondary", size: "sm" }), "gap-1.5")}
            >
              <FileText className="size-3.5" aria-hidden />
              Edit in CMS
            </Link>
            {operationalStatus?.blogSlug ? (
              <Link
                href={`/blog/${operationalStatus.blogSlug}`}
                className={cn(buttonVariants({ variant: "outline", size: "sm" }), "gap-1.5")}
                target="_blank"
                rel="noreferrer"
              >
                <ExternalLink className="size-3.5" aria-hidden />
                View public post
              </Link>
            ) : null}
          </div>
        ) : idea.marketing_status === "approved" ? (
          <div className="grid gap-3">
            {claimsBlockPublish(claims) ? (
              <p className="text-sm text-amber-800 dark:text-amber-200">
                Resolve claims in the{" "}
                <a className="font-medium underline" href="#pipeline-section-claims">
                  evidence ledger
                </a>{" "}
                before publishing.
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">
                Create a published blog post from the approved draft and marketing metadata.
              </p>
            )}
            <div className="flex flex-wrap items-center gap-3">
              <form action={actions.publishToBlog}>
                <input name="ideaId" type="hidden" value={idea.id} />
                <ActionSubmitButton
                  disabled={claimsBlockPublish(claims)}
                  icon={Send}
                  label="Publish to blog"
                  variant="default"
                />
              </form>
              <ScheduleButton ideaId={idea.id} scheduledAt={idea.scheduled_at} />
              <ThumbnailButton ideaId={idea.id} title={idea.title} />
            </div>
          </div>
        ) : (
          <EmptyState message="Approve marketing metadata to enable publishing to the blog." />
        )}
          </PipelineStepShell>

          {/* US-097: Observability — AI run history */}
          {aiRuns.length > 0 ? (
            <div className="rounded-xl border border-border/60">
              <div className="flex items-center gap-2 border-b border-border/40 px-5 py-3">
                <Activity className="size-4 text-muted-foreground" aria-hidden />
                <h2 className="text-sm font-semibold">AI Runs</h2>
                <span className="ml-auto text-[11px] text-muted-foreground">
                  {aiRuns.length} run{aiRuns.length !== 1 ? "s" : ""}
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full table-fixed text-left text-xs">
                  <thead>
                    <tr className="border-b border-border/30 text-muted-foreground">
                      <th className="w-[40%] px-5 py-2.5 font-medium">Prompt</th>
                      <th className="w-[15%] px-3 py-2.5 font-medium">Status</th>
                      <th className="w-[15%] px-3 py-2.5 font-medium">Tokens</th>
                      <th className="w-[15%] px-3 py-2.5 font-medium">Latency</th>
                      <th className="w-[15%] px-3 py-2.5 font-medium">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {aiRuns.map((run) => (
                      <tr
                        key={run.id}
                        className="border-b border-border/20 last:border-0 hover:bg-muted/30"
                      >
                        <td className="px-5 py-2.5 font-medium">
                          {run.prompt_name}
                          <span className="ml-1.5 text-[10px] text-muted-foreground">
                            v{run.prompt_version}
                          </span>
                        </td>
                        <td className="px-3 py-2.5">
                          {run.status === "completed" ? (
                            <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400">
                              <CheckCircle className="size-3" />
                              OK
                            </span>
                          ) : (
                            <span
                              className="inline-flex items-center gap-1 text-red-600 dark:text-red-400"
                              title={run.error_message ?? undefined}
                            >
                              <XCircle className="size-3" />
                              Failed
                            </span>
                          )}
                        </td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {run.total_tokens != null
                            ? run.total_tokens.toLocaleString()
                            : "—"}
                        </td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {run.latency_ms != null
                            ? run.latency_ms < 1000
                              ? `${run.latency_ms}ms`
                              : `${(run.latency_ms / 1000).toFixed(1)}s`
                            : "—"}
                        </td>
                        <td className="px-3 py-2.5 text-muted-foreground">
                          {new Date(run.created_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

// ─── Sub-Components ──────────────────────────────────────────────

function MetaField({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      <p className="mt-1.5 text-sm leading-snug text-foreground [overflow-wrap:anywhere]">{value}</p>
    </div>
  );
}

function EmptyState({
  message,
  action,
}: {
  message: string;
  action?: {
    label: string;
    icon: typeof Sparkles;
    actionName: (formData: FormData) => Promise<void>;
    ideaId: string;
  };
}) {
  return (
    <div className="flex flex-col items-center justify-center py-8 text-center">
      <p className="max-w-md text-sm leading-relaxed text-muted-foreground">{message}</p>
      {action && (
        <form action={action.actionName} className="mt-4">
          <input name="ideaId" type="hidden" value={action.ideaId} />
          <ActionSubmitButton icon={action.icon} label={action.label} variant="outline" />
        </form>
      )}
    </div>
  );
}

function ActionButton({
  action,
  ideaId,
  label,
  icon: Icon,
  variant = "default",
}: {
  action: (formData: FormData) => Promise<void>;
  ideaId: string;
  label: string;
  icon: typeof CheckCircle;
  variant?: "default" | "outline";
}) {
  return (
    <form action={action}>
      <input name="ideaId" type="hidden" value={ideaId} />
      <ActionSubmitButton icon={Icon} label={label} variant={variant} />
    </form>
  );
}

function ActionSubmitButton({
  disabled = false,
  icon: Icon,
  label,
  variant,
}: {
  disabled?: boolean;
  icon: typeof CheckCircle;
  label: string;
  variant: "default" | "outline";
}) {
  const { pending } = useFormStatus();

  return (
    <button
      disabled={pending || disabled}
      className={cn(
        buttonVariants({ size: "sm", variant: variant === "default" ? "default" : "outline" }),
        "flex items-center gap-1.5",
        pending && "pointer-events-none opacity-60"
      )}
      type="submit"
    >
      {pending ? (
        <Loader2 className="size-3.5 animate-spin" aria-hidden />
      ) : (
        <Icon className="size-3.5" aria-hidden />
      )}
      {pending ? `${label}…` : label}
    </button>
  );
}

function ActionButtons({
  approveAction,
  rejectAction,
  ideaId,
  approveLabel,
  rejectLabel,
}: {
  approveAction: (formData: FormData) => Promise<void>;
  rejectAction: (formData: FormData) => Promise<void>;
  ideaId: string;
  approveLabel: string;
  rejectLabel: string;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <ActionButton
        action={approveAction}
        ideaId={ideaId}
        label={approveLabel}
        icon={CheckCircle}
        variant="default"
      />
      <ActionButton
        action={rejectAction}
        ideaId={ideaId}
        label={rejectLabel}
        icon={XCircle}
        variant="outline"
      />
    </div>
  );
}

function OperationalStatusBanner({ status }: { status: OperationalStatus }) {
  const isError = status.opStatus === "error";
  const isQueued = status.opStatus === "queued";
  const isPublish = status.opStage === "publish";

  return (
    <div
      role={isError ? "alert" : "status"}
      className={cn(
        "rounded-lg border px-4 py-3",
        isError
          ? "border-red-200 bg-red-50/80 text-red-900 dark:border-red-900 dark:bg-red-950/20 dark:text-red-200"
          : isQueued
            ? "border-amber-200 bg-amber-50/80 text-amber-900 dark:border-amber-900 dark:bg-amber-950/20 dark:text-amber-200"
            : "border-emerald-200 bg-emerald-50/80 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/20 dark:text-emerald-200",
      )}
    >
      <div className="flex items-start gap-3">
        {isError ? (
          <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden />
        ) : (
          <Sparkles className="mt-0.5 size-4 shrink-0" aria-hidden />
        )}
        <div className="grid min-w-0 flex-1 gap-1">
          <p className="text-sm font-medium">
            {isError
              ? isPublish
                ? "Publish needs attention"
                : "Generation needs attention"
              : isQueued
                ? "Generation queued"
                : isPublish
                  ? "Published to blog"
                  : "Generation completed"}
          </p>
          {status.message ? (
            <p className="text-sm leading-snug opacity-80">{status.message}</p>
          ) : null}
          {status.blogPostId ? (
            <div className="mt-2 flex flex-wrap gap-2">
              <Link
                href={`/admin/blog/${status.blogPostId}/edit`}
                className={cn(buttonVariants({ variant: "secondary", size: "sm" }), "gap-1.5")}
              >
                Edit post
              </Link>
              {status.blogSlug ? (
                <Link
                  href={`/blog/${status.blogSlug}`}
                  className={cn(buttonVariants({ variant: "outline", size: "sm" }), "gap-1.5")}
                  target="_blank"
                  rel="noreferrer"
                >
                  View live
                </Link>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function RegenerateAction({
  actionName,
  ideaId,
  label,
}: {
  actionName: (formData: FormData) => Promise<void>;
  ideaId: string;
  label: string;
}) {
  return (
    <div className="flex flex-col gap-2 rounded-xl border border-amber-200 bg-amber-50/70 p-4 dark:border-amber-900 dark:bg-amber-950/15 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm leading-snug text-amber-900 dark:text-amber-200">
        This output was rejected. Regenerate it when the worker and OpenAI key are ready.
      </p>
      <form action={actionName}>
        <input name="ideaId" type="hidden" value={ideaId} />
        <ActionSubmitButton icon={Sparkles} label={label} variant="outline" />
      </form>
    </div>
  );
}

function MarketingField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-medium text-muted-foreground">
        {label}
      </p>
      <p className="mt-1.5 text-sm leading-snug text-foreground">
        {value}
      </p>
    </div>
  );
}
