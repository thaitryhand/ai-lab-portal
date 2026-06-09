#!/usr/bin/env python3
"""Manual backfill remaining traces that couldn't be auto-matched."""

from __future__ import annotations

import sqlite3
from pathlib import Path

db_path = Path("harness.db")

conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row

# Manual matches: trace_id -> (intake_id, reason)
manual_matches = [
    # US-061 blog social feature traces match to blog social intake cluster (intake 87-93)
    (129, 87, "US-061 story work maps to blog social feature intake"),
    (130, 87, "US-061 Docker backend migration maps to blog social feature intake"),

    # E13 Agents SDK traces (187-218) all map to intake 103 (OpenAI Agents SDK initiative)
    (187, 103, "E13 harness audit maps to Agents SDK initiative intake"),
    (188, 103, "Backlog 17 Celery fix is E13 infrastructure"),
    (189, 103, "Backlog 18 agent name casing is E13 infrastructure"),
    (190, 103, "Agents SDK guardrails (US-095) is E13 work"),
    (191, 103, "AiRunTimingHooks (US-096) is E13 work"),
    (192, 103, "Streaming SSE endpoint is E13 work"),
    (193, 103, "MCP tools integration is E13 work"),
    (194, 103, "MCP DB tools is E13 work"),
    (195, 103, "Streaming frontend UI is E13 work"),
    (196, 103, "MCP tools in streaming is E13 work"),
    (197, 103, "Streaming SSE all stages is E13 work"),
    (198, 103, "Observability dashboard (US-097) is E13 work"),
    (199, 103, "Agent-as-tool multi-agent is E13 work"),
    (200, 103, "E13 closeout docs + E2E tests"),
    (201, 103, "Benchmark streaming vs Celery is E13 work"),
    (202, 103, "News pipeline Agents SDK is E13 work"),
    (203, 103, "E2E news streaming + MCP is E13 work"),
    (204, 103, "Full news pipeline streaming is E13 work"),
    (205, 103, "SEO dashboard is E13 work"),
    (206, 103, "Public site UX is E13 work"),
    (207, 103, "Content Calendar is E13 work"),
    (208, 103, "Technical cleanup is E13 work"),
    (209, 103, "Final polish coverage is E13 work"),
    (210, 103, "Readability Score is E13 work"),
    (211, 103, "Lint tests perf is E13 work"),
    (212, 103, "Coverage push is E13 work"),
    (214, 103, "Phase 1 quick wins is E13 work"),
    (215, 103, "Phase 2 SEO Audit pipeline is E13 work"),
    (216, 103, "Golden Path E2E update is E13 work"),
    (217, 103, "Backfill coverage is E13 work"),
    (218, 103, "E2E verify all systems is E13 work"),

    # Current E2E fix traces
    (240, 113, "Current E2E pipeline test fix session"),

    # Remaining 25: June 4-6 redesign/polish/E2E proof sprint (pre-intake-recording era)
    (128, 87, "Harness audit during blog social / contact features batch"),
    (141, 94, "Admin redesign UX polish batch (micro-interactions intake)"),
    (142, 94, "Admin dashboard redesign batch"),
    (143, 94, "Comments page redesign batch"),
    (144, 94, "Dark mode + sidebar fix batch"),
    (145, 99, "Blog UX enhancements batch (landing audit intake)"),
    (146, 99, "QA smoke + pagination batch"),
    (147, 99, "Nav pill fix batch"),
    (148, 99, "Auth form UX fix batch"),
    (149, 99, "Logout action fix batch"),
    (150, 99, "Home landing redesign batch"),
    (151, 99, "Home spacing polish batch"),
    (152, 99, "Design tokens standardization batch"),
    (153, 99, "Harness audit batch"),
    (154, 99, "Trace quality + n/a markers batch"),
    (155, 99, "Playwright proof-gap spec batch"),
    (156, 99, "E2E proof-gap passes batch"),
    (157, 99, "Blog-social selector fix + responsive batch"),
    (158, 99, "AI Blog Pipeline E2E + JSON fix batch"),
    (159, 99, "Admin-proof-gaps E2E restoration batch"),
    (160, 99, "Admin-proof-gaps E2E restoration batch"),
    (161, 99, "Admin-proof-gaps E2E full restoration batch"),
    (162, 99, "SEO structured data + content batch"),
    (163, 99, "SEO content + OG images batch"),
    (164, 99, "Health monitoring + social share batch"),
]

c = conn.cursor()
matched = 0
for trace_id, intake_id, reason in manual_matches:
    row = conn.execute(
        "SELECT id FROM trace WHERE id = ? AND intake_id IS NULL", (trace_id,)
    ).fetchone()
    if row:
        note_text = f"intake_backfill: {reason}"
        c.execute(
            "UPDATE trace SET intake_id = ?, notes = CASE WHEN notes IS NULL OR notes = '' THEN ? ELSE notes || ' | ' || ? END WHERE id = ?",
            (intake_id, note_text, note_text, trace_id),
        )
        matched += 1

conn.commit()

remaining = conn.execute(
    "SELECT COUNT(*) FROM trace WHERE intake_id IS NULL"
).fetchone()[0]
total = conn.execute("SELECT COUNT(*) FROM trace").fetchone()[0]
linked_pct = round((total - remaining) / total * 100, 1)

print(f"Manual matches applied: {matched}")
print(f"Remaining unlinked: {remaining} of {total} ({linked_pct}% linked)")

if remaining > 0:
    print()
    print("Still unlinked:")
    rows = conn.execute(
        "SELECT id, created_at, story_id, task_summary FROM trace WHERE intake_id IS NULL ORDER BY created_at"
    ).fetchall()
    for r in rows:
        summary = (r["task_summary"] or "")[:90]
        print(f"  trace {r['id']} ({r['created_at']}) story={r['story_id'] or 'none'}: {summary}")

conn.close()
