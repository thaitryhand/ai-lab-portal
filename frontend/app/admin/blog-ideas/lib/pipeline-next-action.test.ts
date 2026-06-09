import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { getPipelineNextAction } from "./pipeline-next-action";

const approvedIdea = {
  status: "approved" as const,
  knowledge_context_status: "approved" as const,
  outline_sections: [{ section: "Intro", points: ["Hook"] }],
  outline_status: "approved",
  draft_markdown: "# Draft",
  draft_status: "approved",
  technical_review: { overall_risk: "low", issues: [], approval_recommendation: "approve" },
  technical_review_status: "approved",
  marketing_metadata: { seo_title: "SEO" },
  marketing_status: "approved",
  seo_audit: { score: 90, issues: [] },
  seo_audit_status: "approved",
  published_blog_post_id: null,
};

describe("pipeline-next-action", () => {
  it("returns approve when idea is pending", () => {
    const action = getPipelineNextAction(
      {
        ...approvedIdea,
        status: "pending",
        outline_sections: [],
        outline_status: null,
        draft_markdown: null,
        draft_status: null,
        technical_review: null,
        technical_review_status: null,
        marketing_metadata: null,
        marketing_status: null,
        seo_audit: null,
        seo_audit_status: null,
      },
      0,
    );
    assert.equal(action.kind, "approve");
    assert.equal(action.approveGate, "idea");
  });

  it("returns processing when a generation job is queued", () => {
    const action = getPipelineNextAction(approvedIdea, 0, {
      opStage: "draft",
      opStatus: "queued",
      taskId: "task-1",
    });
    assert.equal(action.kind, "processing");
    assert.match(action.title, /draft/i);
  });

  it("returns publish when marketing is approved and claims exist", () => {
    const action = getPipelineNextAction(approvedIdea, 2);
    assert.equal(action.kind, "publish");
  });
});
