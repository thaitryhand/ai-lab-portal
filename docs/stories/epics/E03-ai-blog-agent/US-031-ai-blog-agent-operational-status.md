# US-031 AI Blog Agent Operational Status

## Status

implemented

## Lane

normal

## Product Contract

Admin generation actions for the AI Blog Agent should return useful operational feedback instead of silently redirecting. When generation is queued by the backend, the idea detail page shows a queued status with task id. When generation fails or is rejected by the backend, the page shows a safe error message that tells the admin what to fix next.

## Relevant Product Docs

- `docs/product/blog-agent.md`

## Acceptance Criteria

- Generate outline/draft/technical review/marketing actions redirect back with a success notice when the backend queues work (`202`).
- Generation actions redirect back with an error notice when the backend returns a non-OK response.
- Notices are displayed on the idea detail page and do not expose secrets.
- Existing generation endpoints and approval/rejection APIs remain unchanged.
- No schema changes are introduced.

## Design Notes

- Commands: Next.js server actions in `frontend/app/admin/blog-ideas/actions.ts`.
- Queries: idea detail page reads `searchParams` for status messages.
- API: reuse existing backend generation endpoints and parse `202 detail.task_id` when present.
- Tables: no schema change.
- Domain rules: this is operator feedback only; it is not durable task tracking.
- UI surfaces: `frontend/app/admin/blog-ideas/[id]/page.tsx`, `frontend/app/admin/blog-ideas/idea-detail-view.tsx`.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id US-031 --unit 1 --integration 1 --e2e 0 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | Frontend lint/typecheck. |
| Integration | Frontend build and backend blog idea tests. |
| E2E | Not required for this bounded feedback slice. |
| Platform | Not required. |
| Release | Harness trace with validation output. |

## Harness Delta

None expected.

## Evidence

- 2026-06-03:
    - `python -m pytest backend/tests/test_blog_ideas.py` → 32 passed.
    - `cd frontend && npm run lint && npm run typecheck && npm run build` → passed.
    - Generation server actions now redirect back with `queued`, `completed`, or `error` status messages.
    - Idea detail page displays safe operational feedback with stage and task id when available.
    - E2E is marked `n/a` per this story's validation contract: this bounded feedback slice did not require browser E2E.
