export type ApproveGate = "idea" | "collect" | "outline" | "draft" | "review" | "marketing" | "seo";

export type PipelineOpStage =
  | "outline"
  | "draft"
  | "technical-review"
  | "marketing"
  | "seo-audit"
  | "claims";

export type NextPipelineStep = {
  gate: ApproveGate;
  opStage: PipelineOpStage;
  endpoint: (ideaId: string) => string;
  completedMessage: string;
  /** Sync POST (no Celery job polling). */
  synchronous?: boolean;
};

const NEXT_AFTER_APPROVE: Record<ApproveGate, NextPipelineStep> = {
  idea: {
    gate: "idea",
    opStage: "outline",
    endpoint: (ideaId) => `/admin/blog-ideas/${ideaId}/generate-outline`,
    completedMessage: "Outline generation completed.",
  },
  collect: {
    gate: "collect",
    opStage: "outline",
    endpoint: (ideaId) => `/admin/blog-ideas/${ideaId}/generate-outline`,
    completedMessage: "Knowledge context approved. Generating outline.",
  },
  outline: {
    gate: "outline",
    opStage: "draft",
    endpoint: (ideaId) => `/admin/blog-ideas/${ideaId}/generate-draft`,
    completedMessage: "Draft generation completed.",
  },
  draft: {
    gate: "draft",
    opStage: "technical-review",
    endpoint: (ideaId) => `/admin/blog-ideas/${ideaId}/review-technical`,
    completedMessage: "Technical review completed.",
  },
  review: {
    gate: "review",
    opStage: "marketing",
    endpoint: (ideaId) => `/admin/blog-ideas/${ideaId}/generate-marketing`,
    completedMessage: "Marketing metadata generation completed.",
  },
  marketing: {
    gate: "marketing",
    opStage: "seo-audit",
    endpoint: (ideaId) => `/admin/blog-ideas/${ideaId}/audit-seo`,
    completedMessage: "SEO audit completed.",
  },
  seo: {
    gate: "seo",
    opStage: "claims",
    endpoint: (ideaId) => `/admin/blog-ideas/${ideaId}/extract-claims`,
    completedMessage: "Claims extracted from draft.",
    synchronous: true,
  },
};

export function nextStepAfterApprove(gate: ApproveGate): NextPipelineStep {
  return NEXT_AFTER_APPROVE[gate];
}

export function approveButtonLabel(gate: ApproveGate): string {
  switch (gate) {
    case "idea":
      return "Approve & generate outline";
    case "collect":
      return "Approve & generate outline";
    case "outline":
      return "Approve & generate draft";
    case "draft":
      return "Approve & run review";
    case "review":
      return "Accept & generate marketing";
    case "marketing":
      return "Approve & run SEO audit";
    case "seo":
      return "Approve & extract claims";
  }
}
