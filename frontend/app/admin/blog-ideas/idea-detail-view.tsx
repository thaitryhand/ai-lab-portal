"use client";

import { motion } from "framer-motion";
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
  BookOpen,
  Shield,
  Megaphone,
  Lightbulb,
} from "lucide-react";

import { AdminBackLink } from "@/components/admin/admin-back-link";
import {
  adminPageStackClass,
  adminPageTitleClass,
  adminPanelClass,
} from "@/components/admin/admin-ui";
import { buttonVariants } from "@/components/ui/button-variants";
import { cn } from "@/lib/utils";

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
  created_at: string;
  updated_at: string;
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

// ─── Pipeline Stage Config ──────────────────────────────────────

type StageId = "idea" | "outline" | "draft" | "review" | "marketing";

const stages: {
  id: StageId;
  label: string;
  icon: typeof Lightbulb;
  description: string;
}[] = [
  { id: "idea", label: "Idea", icon: Lightbulb, description: "Concept & angle" },
  { id: "outline", label: "Outline", icon: BookOpen, description: "Structure & sections" },
  { id: "draft", label: "Draft", icon: FileText, description: "Full article" },
  { id: "review", label: "Review", icon: Shield, description: "Technical check" },
  { id: "marketing", label: "Marketing", icon: Megaphone, description: "SEO & social" },
];

function getStageStatus(idea: BlogIdeaDetail, stageId: StageId): "done" | "current" | "pending" | "skipped" {
  switch (stageId) {
    case "idea":
      return idea.status === "approved"
        ? "done"
        : idea.status === "rejected"
          ? "skipped"
          : "current";
    case "outline":
      if (idea.outline_status === "approved") return "done";
      if (idea.outline_status === "pending" || idea.outline_status === "rejected") return "current";
      return idea.status === "approved" ? "current" : "pending";
    case "draft":
      if (idea.draft_status === "approved") return "done";
      if (idea.draft_status === "pending" || idea.draft_status === "rejected") return "current";
      if (idea.outline_status === "approved") return "current";
      return "pending";
    case "review":
      if (idea.technical_review_status === "approved") return "done";
      if (idea.technical_review_status === "pending" || idea.technical_review_status === "rejected") return "current";
      if (idea.draft_status === "approved") return "current";
      return "pending";
    case "marketing":
      if (idea.marketing_status === "approved") return "done";
      if (idea.marketing_status === "pending" || idea.marketing_status === "rejected") return "current";
      if (idea.draft_status === "approved") return "current";
      return "pending";
  }
}

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
};

// ─── Main Component ──────────────────────────────────────────────

type Props = {
  idea: BlogIdeaDetail;
  actions: Actions;
};

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};

const sectionAnim = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } },
};

export function BlogIdeaDetailView({ idea, actions }: Props) {
  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className={adminPageStackClass}
    >
      <motion.div variants={sectionAnim}>
        <AdminBackLink href="/admin/blog-ideas">Back to ideas</AdminBackLink>
      </motion.div>

      {/* ── Pipeline progress ── */}
      <motion.div
        variants={sectionAnim}
        className={adminPanelClass}
      >
        <div className="flex items-center justify-between gap-2">
          {stages.map((stage, i) => {
            const stageStatus = getStageStatus(idea, stage.id);
            const Icon = stage.icon;
            return (
              <div key={stage.id} className="flex flex-1 items-center gap-2">
                <div className="flex flex-col items-center gap-1.5 sm:flex-row">
                  <span
                    className={cn(
                      "flex size-8 shrink-0 items-center justify-center rounded-md text-xs font-bold transition-colors duration-200",
                      stageStatus === "done"
                        ? "bg-brand text-white"
                        : stageStatus === "current"
                          ? "border-2 border-brand bg-card text-brand"
                          : stageStatus === "skipped"
                            ? "bg-red-100 text-red-500 dark:bg-red-950/30 dark:text-red-400"
                            : "bg-muted text-muted-foreground"
                    )}
                  >
                    {stageStatus === "done" ? (
                      <CheckCircle className="size-4" />
                    ) : (
                      <Icon className="size-4" />
                    )}
                  </span>
                  <div className="hidden sm:block">
                    <p
                      className={cn(
                        "text-xs font-semibold leading-tight",
                        stageStatus === "done"
                          ? "text-brand"
                          : stageStatus === "current"
                            ? "text-foreground"
                            : "text-muted-foreground"
                      )}
                    >
                      {stage.label}
                    </p>
                    <p className="text-[10px] text-muted-foreground">
                      {stage.description}
                    </p>
                  </div>
                </div>
                {i < stages.length - 1 && (
                  <div
                    className={cn(
                      "hidden h-px flex-1 sm:block",
                      stageStatus === "done"
                        ? "bg-brand"
                        : "bg-border"
                    )}
                  />
                )}
              </div>
            );
          })}
        </div>
      </motion.div>

      {/* ── Header ── */}
      <motion.div variants={sectionAnim}>
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className={cn(
                "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium",
                statusColors[idea.status]
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
              Created {formatDate(idea.created_at)}
            </span>
          </div>
          <h1 className={adminPageTitleClass}>
            {idea.title}
          </h1>
        </div>
      </motion.div>

      {/* ── Metadata ── */}
      <motion.div
        variants={sectionAnim}
        className={adminPanelClass}
      >
        <div className="grid gap-5 sm:grid-cols-3">
          <div>
            <p className="text-xs font-medium text-muted-foreground">
              Angle
            </p>
            <p className="mt-1.5 text-sm leading-snug text-foreground">
              {idea.angle}
            </p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">
              Target reader
            </p>
            <p className="mt-1.5 text-sm leading-snug text-foreground">
              {idea.target_reader}
            </p>
          </div>
          <div>
            <p className="text-xs font-medium text-muted-foreground">
              Article goal
            </p>
            <p className="mt-1.5 text-sm leading-snug text-foreground">
              {idea.article_goal}
            </p>
          </div>
        </div>

        {idea.positioning_notes.length > 0 && (
          <>
            <hr className="my-4 border-border " />
            <div>
              <p className="text-xs font-medium text-muted-foreground">
                Positioning notes
              </p>
              <ul className="mt-2 space-y-1">
                {idea.positioning_notes.map((note, i) => (
                  <li
                    key={`note-${note.slice(0, 24)}-${i}`}
                    className="flex items-start gap-2 text-sm leading-snug text-foreground"
                  >
                    <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-brand" />
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}

        {idea.feedback && (
          <>
            <hr className="my-4 border-border " />
            <div>
              <p className="text-xs font-medium text-muted-foreground">
                Feedback
              </p>
              <p className="mt-1.5 text-sm italic leading-snug text-muted-foreground">
                {idea.feedback}
              </p>
            </div>
          </>
        )}
      </motion.div>

      {/* ── Outline Section ── */}
      <SectionCard
        icon={BookOpen}
        label="Outline"
        status={idea.outline_status}
        statusColors={statusColors}
      >
        {idea.outline_sections.length === 0 ? (
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
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {idea.outline_status === "pending" && (
              <ActionButtons
                approveAction={actions.approveOutline}
                rejectAction={actions.rejectOutline}
                ideaId={idea.id}
                approveLabel="Approve outline"
                rejectLabel="Reject outline"
              />
            )}
            {idea.outline_status === "approved" && (
              <StatusDone label="Outline approved" />
            )}
            {idea.outline_status === "rejected" && idea.status === "approved" && (
              <RegenerateAction
                actionName={actions.generateOutline}
                ideaId={idea.id}
                label="Regenerate outline"
              />
            )}
            <div className="grid gap-5">
              {idea.outline_sections.map((section, i) => (
                <div key={section.section} className="rounded-xl border border-border bg-muted/50 p-4">
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
                        className="flex items-start gap-2 text-sm leading-snug text-muted-foreground"
                      >
                        <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-muted-foreground/40" />
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        )}
      </SectionCard>

      {/* ── Draft Section ── */}
      <SectionCard
        icon={FileText}
        label="Draft"
        status={idea.draft_status}
        statusColors={statusColors}
      >
        {!idea.draft_markdown ? (
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
        ) : (
          <div className="grid gap-4">
            {idea.draft_status === "pending" && (
              <ActionButtons
                approveAction={actions.approveDraft}
                rejectAction={actions.rejectDraft}
                ideaId={idea.id}
                approveLabel="Approve draft"
                rejectLabel="Reject draft"
              />
            )}
            {idea.draft_status === "approved" && (
              <StatusDone label="Draft approved" />
            )}
            {idea.draft_status === "rejected" && idea.outline_status === "approved" && (
              <RegenerateAction
                actionName={actions.generateDraft}
                ideaId={idea.id}
                label="Regenerate draft"
              />
            )}
            <div className="prose prose-sm prose-green max-w-none rounded-xl border border-border bg-muted/30 p-5">
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
      </SectionCard>

      {/* ── Technical Review Section ── */}
      <SectionCard
        icon={Shield}
        label="Technical Review"
        status={idea.technical_review_status}
        statusColors={statusColors}
      >
        {!idea.technical_review ? (
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

            {idea.technical_review_status === "pending" && (
              <ActionButtons
                approveAction={actions.approveReview}
                rejectAction={actions.rejectReview}
                ideaId={idea.id}
                approveLabel="Accept review"
                rejectLabel="Request changes"
              />
            )}
            {idea.technical_review_status === "approved" && (
              <StatusDone label="Review accepted" />
            )}
            {idea.technical_review_status === "rejected" && idea.draft_status === "approved" && (
              <RegenerateAction
                actionName={actions.reviewTechnical}
                ideaId={idea.id}
                label="Run review again"
              />
            )}

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
                        <p className="text-sm leading-snug text-foreground">
                          <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                            Text:
                          </span>{" "}
                          {issue.text}
                        </p>
                        <p className="text-sm leading-snug text-muted-foreground">
                          <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
                            Issue:
                          </span>{" "}
                          {issue.reason}
                        </p>
                        <p className="text-sm leading-snug italic text-brand">
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
      </SectionCard>

      {/* ── Marketing Section ── */}
      <SectionCard
        icon={Megaphone}
        label="Marketing"
        status={idea.marketing_status}
        statusColors={statusColors}
      >
        {!idea.marketing_metadata ? (
          <EmptyState
            message={
              idea.draft_status === "approved"
                ? "No marketing metadata yet. Generation requires the worker and OpenAI key to be configured."
                : "Approve the draft first to enable marketing generation."
            }
            action={
              idea.draft_status === "approved" && !idea.marketing_status
                ? {
                    label: "Generate marketing metadata",
                    icon: Sparkles,
                    actionName: actions.generateMarketing,
                    ideaId: idea.id,
                  }
                : undefined
            }
          />
        ) : (
          <div className="grid gap-4">
            {idea.marketing_status === "pending" && (
              <ActionButtons
                approveAction={actions.approveMarketing}
                rejectAction={actions.rejectMarketing}
                ideaId={idea.id}
                approveLabel="Approve marketing"
                rejectLabel="Regenerate"
              />
            )}
            {idea.marketing_status === "approved" && (
              <StatusDone label="Marketing approved" />
            )}
            {idea.marketing_status === "rejected" && idea.draft_status === "approved" && (
              <RegenerateAction
                actionName={actions.generateMarketing}
                ideaId={idea.id}
                label="Regenerate marketing"
              />
            )}

            <div className="grid gap-5">
              <MarketingField
                label="SEO Title"
                value={idea.marketing_metadata.seo_title}
              />
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
          </div>
        )}
      </SectionCard>
    </motion.div>
  );
}

// ─── Sub-Components ──────────────────────────────────────────────

function SectionCard({
  icon: Icon,
  label,
  status,
  statusColors,
  children,
}: {
  icon: typeof Lightbulb;
  label: string;
  status: string | null;
  statusColors: Record<string, string>;
  children: React.ReactNode;
}) {
  return (
    <motion.div
      variants={sectionAnim}
      className={cn(adminPanelClass, "p-0")}
    >
      <div className="flex items-center justify-between border-b border-border px-5 py-4 ">
        <div className="flex items-center gap-2.5">
          <div className="flex size-8 items-center justify-center rounded-xl bg-muted">
            <Icon className="size-4 text-muted-foreground" aria-hidden />
          </div>
          <h2 className="text-sm font-semibold text-foreground">
            {label}
          </h2>
        </div>
        {status && (
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-widest",
              statusColors[status] ?? statusColors.pending
            )}
          >
            {status === "approved" && <CheckCircle className="size-3" />}
            {status === "rejected" && <XCircle className="size-3" />}
            {status === "pending" && <Clock className="size-3" />}
            {status}
          </span>
        )}
      </div>
      <div className="p-5">{children}</div>
    </motion.div>
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
      <p className="text-sm text-muted-foreground">{message}</p>
      {action && (
        <form action={action.actionName} className="mt-4">
          <input name="ideaId" type="hidden" value={action.ideaId} />
          <button
            className={cn(buttonVariants({ variant: "secondary" }), "gap-2")}
            type="submit"
          >
            <action.icon className="size-4" aria-hidden />
            {action.label}
          </button>
        </form>
      )}
    </div>
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
      <form action={approveAction}>
        <input name="ideaId" type="hidden" value={ideaId} />
        <button
          className={cn(
            buttonVariants({ size: "sm" }),
            "flex items-center gap-1.5 rounded-md bg-brand px-3 py-1.5 text-xs font-medium text-white hover:bg-brand/90"
          )}
          type="submit"
        >
          <CheckCircle className="size-3.5" aria-hidden />
          {approveLabel}
        </button>
      </form>
      <form action={rejectAction}>
        <input name="ideaId" type="hidden" value={ideaId} />
        <button
          className={cn(
            buttonVariants({ size: "sm", variant: "outline" }),
            "flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted"
          )}
          type="submit"
        >
          <XCircle className="size-3.5" aria-hidden />
          {rejectLabel}
        </button>
      </form>
    </div>
  );
}

function StatusDone({ label }: { label: string }) {
  return (
    <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-widest text-emerald-600 dark:text-emerald-400">
      <CheckCircle className="size-3.5" aria-hidden />
      {label}
    </p>
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
        <button
          className={cn(buttonVariants({ size: "sm", variant: "secondary" }), "gap-1.5 whitespace-nowrap")}
          type="submit"
        >
          <Sparkles className="size-3.5" aria-hidden />
          {label}
        </button>
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
