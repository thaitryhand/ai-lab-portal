import {
  approveButtonLabel,
  type ApproveGate,
} from "./pipeline-next-stage";

export type PipelineStageId =
  | "idea"
  | "outline"
  | "draft"
  | "review"
  | "marketing"
  | "seo"
  | "claims"
  | "publish";

export type PipelineActionKind =
  | "approve"
  | "generate"
  | "processing"
  | "claims"
  | "publish"
  | "done"
  | "blocked";

export type IdeaPipelineSnapshot = {
  status: "pending" | "approved" | "rejected";
  outline_sections: unknown[];
  outline_status: string | null;
  draft_markdown: string | null;
  draft_status: string | null;
  technical_review: unknown | null;
  technical_review_status: string | null;
  marketing_metadata: unknown | null;
  marketing_status: string | null;
  seo_audit: unknown | null;
  seo_audit_status: string | null;
  published_blog_post_id: string | null;
};

export type OperationalSnapshot = {
  opStage?: string;
  opStatus?: string;
  taskId?: string;
};

export type PipelineNextAction = {
  kind: PipelineActionKind;
  stageId: PipelineStageId;
  title: string;
  description: string;
  approveGate?: ApproveGate;
  sectionAnchor: string;
};

const PROCESSING_LABELS: Record<string, string> = {
  idea: "Generating blog idea",
  outline: "Generating outline",
  draft: "Writing draft",
  "technical-review": "Running technical review",
  marketing: "Generating marketing metadata",
  "seo-audit": "Running SEO audit",
  claims: "Extracting claims",
};

function isProcessing(op?: OperationalSnapshot): boolean {
  return (
    !!op?.taskId &&
    (op.opStatus === "queued" || op.opStatus === "running")
  );
}

export function getPipelineNextAction(
  idea: IdeaPipelineSnapshot,
  claimsCount: number,
  op?: OperationalSnapshot,
): PipelineNextAction {
  if (idea.published_blog_post_id) {
    return {
      kind: "done",
      stageId: "publish",
      title: "Published",
      description: "This idea is linked to a blog post.",
      sectionAnchor: "pipeline-section-publish",
    };
  }

  if (isProcessing(op)) {
    const stage = op?.opStage ?? "outline";
    return {
      kind: "processing",
      stageId: stageToStageId(stage),
      title: PROCESSING_LABELS[stage] ?? "Running pipeline step",
      description: "Generation is in progress. This page will refresh when it completes.",
      sectionAnchor: stageToAnchor(stage),
    };
  }

  if (idea.status === "pending") {
    return {
      kind: "approve",
      stageId: "idea",
      title: "Approve the idea",
      description: approveButtonLabel("idea"),
      approveGate: "idea",
      sectionAnchor: "pipeline-section-idea",
    };
  }

  if (idea.status === "rejected") {
    return {
      kind: "blocked",
      stageId: "idea",
      title: "Idea rejected",
      description: "Reject clears this path. Create a new idea or revise manually if supported.",
      sectionAnchor: "pipeline-section-idea",
    };
  }

  if (idea.outline_status === "pending" && idea.outline_sections.length > 0) {
    return {
      kind: "approve",
      stageId: "outline",
      title: "Review the outline",
      description: approveButtonLabel("outline"),
      approveGate: "outline",
      sectionAnchor: "pipeline-section-outline",
    };
  }

  if (idea.outline_status === "rejected" || idea.outline_sections.length === 0) {
    return {
      kind: "generate",
      stageId: "outline",
      title: idea.outline_sections.length === 0 ? "Generate outline" : "Regenerate outline",
      description: "Outline generation requires the worker and OpenAI key.",
      sectionAnchor: "pipeline-section-outline",
    };
  }

  if (idea.draft_status === "pending" && idea.draft_markdown) {
    return {
      kind: "approve",
      stageId: "draft",
      title: "Review the draft",
      description: approveButtonLabel("draft"),
      approveGate: "draft",
      sectionAnchor: "pipeline-section-draft",
    };
  }

  if (idea.draft_status === "rejected" || !idea.draft_markdown) {
    return {
      kind: "generate",
      stageId: "draft",
      title: !idea.draft_markdown ? "Generate draft" : "Regenerate draft",
      description: "Draft generation requires the worker and OpenAI key.",
      sectionAnchor: "pipeline-section-draft",
    };
  }

  if (!idea.technical_review && !idea.technical_review_status) {
    return {
      kind: "generate",
      stageId: "review",
      title: "Run technical review",
      description: "Automated review checks factual and technical risk in the draft.",
      sectionAnchor: "pipeline-section-review",
    };
  }

  if (idea.technical_review_status === "pending" && idea.technical_review) {
    return {
      kind: "approve",
      stageId: "review",
      title: "Review technical findings",
      description: approveButtonLabel("review"),
      approveGate: "review",
      sectionAnchor: "pipeline-section-review",
    };
  }

  if (idea.technical_review_status === "rejected") {
    return {
      kind: "generate",
      stageId: "review",
      title: "Run review again",
      description: "Address draft issues, then re-run technical review.",
      sectionAnchor: "pipeline-section-review",
    };
  }

  if (!idea.marketing_metadata && idea.technical_review_status === "approved") {
    return {
      kind: "generate",
      stageId: "marketing",
      title: "Generate marketing metadata",
      description: "SEO title, meta description, and social copy for publish.",
      sectionAnchor: "pipeline-section-marketing",
    };
  }

  if (idea.marketing_status === "pending" && idea.marketing_metadata) {
    return {
      kind: "approve",
      stageId: "marketing",
      title: "Review marketing metadata",
      description: approveButtonLabel("marketing"),
      approveGate: "marketing",
      sectionAnchor: "pipeline-section-marketing",
    };
  }

  if (idea.marketing_status === "rejected") {
    return {
      kind: "generate",
      stageId: "marketing",
      title: "Regenerate marketing metadata",
      description: "Marketing generation requires the worker and OpenAI key.",
      sectionAnchor: "pipeline-section-marketing",
    };
  }

  if (!idea.seo_audit && !idea.seo_audit_status && idea.marketing_status === "approved") {
    return {
      kind: "generate",
      stageId: "seo",
      title: "Run SEO audit",
      description: "Automated SEO audit checks title, meta description, headings, keywords, and readability.",
      sectionAnchor: "pipeline-section-seo",
    };
  }

  if (idea.seo_audit_status === "pending" && idea.seo_audit) {
    return {
      kind: "approve",
      stageId: "seo",
      title: "Review SEO audit findings",
      description: approveButtonLabel("seo"),
      approveGate: "seo",
      sectionAnchor: "pipeline-section-seo",
    };
  }

  if (idea.seo_audit_status === "rejected") {
    return {
      kind: "generate",
      stageId: "seo",
      title: "Run SEO audit again",
      description: "Address SEO issues, then re-run the audit.",
      sectionAnchor: "pipeline-section-seo",
    };
  }

  if (
    idea.seo_audit_status === "approved"
    && idea.marketing_status === "approved"
    && idea.technical_review_status === "approved"
    && claimsCount === 0
  ) {
    return {
      kind: "claims",
      stageId: "claims",
      title: "Extract claims",
      description: "Claims were not extracted yet. Approve SEO audit again or extract manually.",
      sectionAnchor: "pipeline-section-claims",
    };
  }

  if (idea.seo_audit_status === "approved" && idea.marketing_status === "approved" && idea.technical_review_status === "approved") {
    return {
      kind: "publish",
      stageId: "publish",
      title: "Publish to blog",
      description: "Create a published blog post from the approved draft and marketing metadata.",
      sectionAnchor: "pipeline-section-publish",
    };
  }

  return {
    kind: "done",
    stageId: "publish",
    title: "Pipeline complete",
    description: "All gates are cleared.",
    sectionAnchor: "pipeline-section-publish",
  };
}

function stageToStageId(stage: string): PipelineStageId {
  switch (stage) {
    case "outline":
      return "outline";
    case "draft":
      return "draft";
    case "technical-review":
      return "review";
    case "marketing":
      return "marketing";
    case "seo-audit":
      return "seo";
    case "claims":
      return "claims";
    default:
      return "idea";
  }
}

function stageToAnchor(stage: string): string {
  switch (stage) {
    case "outline":
      return "pipeline-section-outline";
    case "draft":
      return "pipeline-section-draft";
    case "technical-review":
      return "pipeline-section-review";
    case "marketing":
      return "pipeline-section-marketing";
    case "seo-audit":
      return "pipeline-section-seo";
    case "claims":
      return "pipeline-section-claims";
    default:
      return "pipeline-section-idea";
  }
}
