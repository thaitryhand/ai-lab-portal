import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  mapProjectToGeneratePayload,
  mapShowcaseToGeneratePayload,
} from "./map-context-to-generate";

describe("map-context-to-generate", () => {
  it("maps project fields to generate payload", () => {
    const payload = mapProjectToGeneratePayload({
      title: "Scopelytics",
      description: "Analytics for game studios",
      content_markdown: "## Architecture\nUses embeddings.",
    });

    assert.equal(payload.project_name, "Scopelytics");
    assert.equal(payload.project_summary, "Analytics for game studios");
    assert.match(payload.technical_highlights, /Architecture/);
    assert.equal(payload.business_value, "Analytics for game studios");
  });

  it("maps showcase fields to generate payload", () => {
    const payload = mapShowcaseToGeneratePayload({
      title: "Retail Copilot",
      hero_summary: "In-store assistant for staff",
      industry: "Retail",
      use_case: "Product lookup",
      content_markdown: "Long case study body",
    });

    assert.equal(payload.project_name, "Retail Copilot");
    assert.equal(payload.project_summary, "In-store assistant for staff");
    assert.equal(payload.ai_capabilities, "Product lookup — Retail");
    assert.equal(payload.business_value, "Retail");
  });
});
