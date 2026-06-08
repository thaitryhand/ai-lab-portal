import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { emptyStats, formatTime, stageLabel } from "./helpers";

describe("ai-observability helpers", () => {
  describe("emptyStats", () => {
    it("returns zeroed stats", () => {
      const stats = emptyStats();
      assert.equal(stats.total_runs, 0);
      assert.equal(stats.completed, 0);
      assert.equal(stats.failed, 0);
      assert.equal(stats.success_rate, 0);
      assert.equal(stats.avg_latency_ms, 0);
      assert.equal(stats.avg_total_tokens, 0);
      assert.equal(stats.total_tokens, 0);
      assert.deepEqual(stats.stages, {});
    });
  });

  describe("formatTime", () => {
    it("formats an ISO date string", () => {
      const result = formatTime("2026-06-08T12:30:00Z");
      assert.ok(result.includes("Jun"));
      assert.ok(result.includes("8"));
      assert.ok(result.length > 0);
    });

    it("handles midnight time", () => {
      const result = formatTime("2026-01-01T00:00:00Z");
      assert.ok(result.includes("Jan"));
      assert.ok(result.includes("1"));
    });
  });

  describe("stageLabel", () => {
    it("returns known labels", () => {
      assert.equal(stageLabel("blog_idea"), "Idea");
      assert.equal(stageLabel("blog_outline"), "Outline");
      assert.equal(stageLabel("draft_writer"), "Draft");
      assert.equal(stageLabel("draft_section_writer"), "Draft (section)");
      assert.equal(stageLabel("technical_review"), "Review");
      assert.equal(stageLabel("marketing_metadata"), "Marketing");
      assert.equal(stageLabel("claim_extraction"), "Claims");
      assert.equal(stageLabel("ai_news_scoring"), "News scoring");
    });

    it("falls back to the raw name for unknown stages", () => {
      assert.equal(stageLabel("custom_stage"), "custom_stage");
      assert.equal(stageLabel(""), "");
    });
  });
});
