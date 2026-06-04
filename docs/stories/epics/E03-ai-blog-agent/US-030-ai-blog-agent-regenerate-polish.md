# US-030 AI Blog Agent Regenerate Polish

## Status

implemented

## Lane

normal

## Product Contract

Admin users can recover from rejected AI Blog Agent outputs without leaving the detail page. If an outline, draft, technical review, or marketing metadata is rejected, the UI offers a clear regenerate action that reuses the existing generation endpoint for that stage. Empty generation states also explain that async generation requires the worker and OpenAI key to be configured.

## Relevant Product Docs

- `docs/product/blog-agent.md`
- `docs/product/mvp-roadmap.md`

## Acceptance Criteria

- Rejected outline state shows a "Regenerate outline" action.
- Rejected draft state shows a "Regenerate draft" action.
- Rejected technical review state shows a "Run review again" action.
- Rejected marketing metadata state shows a "Regenerate marketing" action.
- Empty generation states mention worker/OpenAI key readiness without exposing secrets.
- Existing approve/reject actions remain unchanged.

## Design Notes

- Commands: existing Next.js server actions in `frontend/app/admin/blog-ideas/actions.ts`.
- Queries: existing detail page fetch.
- API: reuse existing FastAPI generation endpoints.
- Tables: no schema change.
- Domain rules: regeneration is available only after the prior prerequisite is approved.
- UI surfaces: `frontend/app/admin/blog-ideas/idea-detail-view.tsx`.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id US-030 --unit 1 --integration 1 --e2e 0 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | Frontend lint/typecheck. |
| Integration | Frontend build plus relevant backend blog idea tests. |
| E2E | Not required for this UI-only polish unless selectors change. |
| Platform | Not required. |
| Release | Harness trace with changed files and validation output. |

## Harness Delta

None expected.

## Evidence

- 2026-06-03:
    - `python -m pytest backend/tests/test_blog_ideas.py` → 32 passed.
    - `cd frontend && npm run lint && npm run typecheck && npm run build` → passed.
    - UI adds regeneration affordances for rejected outline, draft, technical review, and marketing stages.
    - Product roadmap updated to mark MVP 2 as in progress with delivered AI-assisted blog workflow pieces.
    - E2E is marked `n/a` per this story's validation contract: selector-changing browser proof was not required for this bounded UI polish.
