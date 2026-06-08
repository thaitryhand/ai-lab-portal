import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  approveButtonLabel,
  nextStepAfterApprove,
} from "./pipeline-next-stage";

describe("pipeline-next-stage", () => {
  it("maps approve gates to the next pipeline generation step", () => {
    assert.equal(nextStepAfterApprove("idea").opStage, "outline");
    assert.equal(nextStepAfterApprove("outline").opStage, "draft");
    assert.equal(nextStepAfterApprove("draft").opStage, "technical-review");
    assert.equal(nextStepAfterApprove("review").opStage, "marketing");
    assert.equal(nextStepAfterApprove("seo").synchronous, true);
  });

  it("returns human-readable approve labels", () => {
    assert.match(approveButtonLabel("outline"), /generate draft/i);
  });
});
