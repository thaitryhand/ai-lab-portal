# US-084 Generate from Context UI

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — Phase 1 intake (2026-06-06).

## Product Contract

Admin operators can start the AI blog pipeline by generating an idea from real
Project or Showcase content instead of typing title/angle manually.

## Acceptance Criteria

1. `/admin/blog-ideas/new` exposes a **Generate from context** flow (default tab).
2. Submitting calls `POST /admin/blog-ideas/generate` with mapped context fields.
3. On synchronous success, redirect to `/admin/blog-ideas/{id}`.
4. On async (202) response, show job polling UI then redirect to the new idea.
5. Manual create flow remains available on the same page.
6. Frontend typecheck, lint, and build pass.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Context mapping helper tests (optional) |
| Integration | Existing `/admin/blog-ideas/generate` contract |
| E2E | Covered by US-086 |
| Platform | N/A |
| Release | Frontend quality gate |

## Evidence

- (pending implementation)
