# US-048 Admin AI News Review UI

## Status

implemented

## Lane

normal

## Product Contract

Admins can review AI News candidates from the admin shell without calling the API manually. The UI exposes scored candidates, status, score context, and bounded actions for approve, reject, publish, and unpublish using the existing admin review endpoints.

## Relevant Product Docs

- `docs/product/news-intelligence.md`
- `docs/product/overview.md`
- `docs/product/mvp-roadmap.md`

## Acceptance Criteria

- Admin navigation includes an AI News review queue entry distinct from source configuration.
- `/admin/news-review` lists review items with status, score, source, summary, and why-it-matters context.
- Pending candidates can be approved or rejected from the list.
- Approved candidates can be published; published candidates can be unpublished and linked to their public page.
- Empty review queue state explains how candidates arrive.

## Design Notes

- Commands: none.
- Queries: server-rendered admin fetch against `/admin/news/review-items`.
- API: no new backend API shape; use existing approve/reject/publish/unpublish endpoints.
- Tables: none.
- Domain rules: UI must not bypass existing admin boundary headers.
- UI surfaces: admin shell navigation and `/admin/news-review` list.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Existing backend review/publish tests remain green. |
| Integration | Frontend typecheck/lint/build validates route and server actions. |
| E2E | Existing admin shell E2E/build route discovery; no new browser automation required for this slice. |
| Platform | Not required. |
| Release | `harness-cli story verify US-048` passes. |

## Harness Delta

None expected.

## Evidence

- `python -m pytest backend/tests/test_news_scoring.py backend/tests/test_news_publish.py` — 8 passed.
- `cd frontend && npm run typecheck` — passed.
- `cd frontend && npm run lint` — passed.
- `cd frontend && npm run build` — passed and listed `/admin/news-review`.
