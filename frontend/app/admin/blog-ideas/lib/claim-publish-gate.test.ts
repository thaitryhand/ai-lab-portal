import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { claimsBlockPublish, summarizeClaims } from "./claim-publish-gate";

describe("claim-publish-gate", () => {
  it("counts blocking pending and unsupported claims", () => {
    const summary = summarizeClaims([
      { status: "pending" },
      { status: "supported" },
      { status: "unsupported" },
      { status: "waived" },
    ]);
    assert.equal(summary.blocking, 2);
    assert.equal(summary.pending, 1);
    assert.equal(summary.unsupported, 1);
  });

  it("returns false when all claims are cleared", () => {
    assert.equal(
      claimsBlockPublish([{ status: "supported" }, { status: "waived" }]),
      false,
    );
  });
});
