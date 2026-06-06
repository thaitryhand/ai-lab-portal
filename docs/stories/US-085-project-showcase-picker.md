# US-085 Project and Showcase Picker

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — Phase 1 intake (2026-06-06).

## Product Contract

The generate UI loads published Projects and Showcases for selection. Project
is the default source type; Showcase is available as secondary context.

## Acceptance Criteria

1. Picker lists admin Projects and Showcases (id + title + status).
2. Default source type is **Project** when both exist.
3. Selected item detail is fetched server-side and mapped to generate payload
   (`project_name`, `project_summary`, `ai_capabilities`, `technical_highlights`,
   `business_value`).
4. Empty lists show helpful empty state with links to create content.
5. Frontend typecheck, lint, and build pass.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Mapping helper for project/showcase → generate request |
| Integration | Admin project/showcase detail fetch |
| E2E | Covered by US-086 |
| Platform | N/A |
| Release | Frontend quality gate |

## Evidence

- (pending implementation)
