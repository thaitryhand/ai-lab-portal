# US-047 Public AI News Topic Filter

## Status

implemented

## Lane

normal

## Product Contract

Public users can filter the `/ai-news` feed by topic without leaving the public AI News surface. The filter uses published-item metadata derived by the feed boundary and keeps the unfiltered feed available.

## Relevant Product Docs

- `docs/product/news-intelligence.md`
- `docs/product/mvp-roadmap.md`
- `docs/product/overview.md`

## Acceptance Criteria

- `/public/ai-news` returns a stable `topic` value for each published news summary/detail.
- `/public/ai-news?topic=<topic>` returns only published items for that topic and rejects no items when the topic is omitted.
- `/ai-news` renders topic filter links and preserves an accessible selected state.
- Empty filtered results explain that no published items match the selected topic.

## Design Notes

- Commands: none.
- Queries: add an optional public AI news topic query parameter.
- API: extend public AI news summary/detail DTOs with `topic`.
- Tables: no schema change; derive the topic at the public boundary for this slice.
- Domain rules: use a small deterministic topic classifier over title, summary, why-it-matters, and source name until durable topics/tags exist.
- UI surfaces: `/ai-news` topic links.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id <id> --unit 1 --integration 1 --e2e 0 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | Topic classifier/filter tests in `backend/tests/test_news_publish.py`. |
| Integration | Public `/public/ai-news?topic=...` API test. |
| E2E | Frontend build/typecheck; existing public shell coverage if available. |
| Platform | Not required for this slice. |
| Release | Story verify after proof commands pass. |

## Harness Delta

None expected.

## Evidence

- `python -m pytest backend/tests/test_news_publish.py` — 4 passed.
- `python -m pytest backend/tests/test_news_publish.py backend/tests/test_news_submitted_links.py` — 9 passed.
- `cd frontend && npm run typecheck` — passed.
- `cd frontend && npm run lint` — passed.
- `cd frontend && npm run build` — passed.
