# US-037 RSS Crawl and Raw Item Storage

## Status

implemented

## Lane

normal

## Product Contract

Enabled RSS-type news sources are fetched on a schedule (or manual admin trigger).
Each feed entry is stored as a raw source item linked to its source, with stable
external identity for idempotent re-crawl. Source `last_crawled_at` updates on
successful runs. Non-RSS source types are skipped in this story.

## Relevant Product Docs

- `docs/product/news-intelligence.md` (pipeline step: Crawler → Raw source item store)
- `docs/product/mvp-roadmap.md` (MVP 3)
- `docs/ARCHITECTURE.md` (Celery workers, SSRF: fetch in workers only)

## Acceptance Criteria

- Alembic migration adds `news_raw_items` (or equivalent) with: `id`, `source_id`,
  `external_id`, `title`, `link_url`, `published_at`, `raw_payload` (JSON/text),
  `content_hash`, `fetched_at`, unique constraint on `(source_id, external_id)`.
- Celery task `news.crawl_rss_source` fetches one enabled RSS source by id using
  `http`/`https` only, timeout and size limits, no inline fetch in API handlers.
- Celery task `news.crawl_due_sources` selects enabled RSS sources past
  `crawl_frequency_minutes` and enqueues per-source crawls.
- Admin API `POST /admin/news-sources/{id}/crawl` triggers a crawl for one source
  (RSS only; 400 for unsupported types).
- Duplicate entries (same `source_id` + `external_id`) upsert or skip without error.
- `last_crawled_at` on `news_sources` updates after a successful crawl.
- Unit/integration tests use a local RSS fixture or mocked HTTP; no live network in CI.

## Design Notes

- Build on `backend/app/news_sources.py` and `news_sources` table (US-036).
- Prefer stdlib + existing deps; add `feedparser` only if justified in `pyproject`/deps.
- SSRF: validate URL scheme/host before fetch; follow redirect limits in worker.
- Optional admin UI: “Crawl now” on source card (can be follow-up if API-only ships first).

## Out of Scope (later stories)

- Firecrawl / article body extraction (US-038+).
- GitHub releases and website crawlers.
- Deduplication across sources, scoring, review queue, public `/ai-news`.

## Validation

Planned verify command:

```bash
python -m pytest backend/tests/test_news_crawl.py
```

| Layer | Expected proof |
| --- | --- |
| Unit | RSS parse, idempotency, URL validation helpers |
| Integration | Crawl task + admin trigger + DB rows |
| E2E | Not required |
| Platform | Not required |

## Harness Delta

- Story added to durable matrix as `planned`.
- Update `docs/stories/backlog.md` and `docs/TEST_MATRIX.md` when implemented.

## Evidence

- 2026-06-03: `python -m pytest backend/tests/test_news_crawl.py` → 6 passed.
- Celery: `news.crawl_rss_source`, `news.crawl_due_sources`.
- Admin: `POST /admin/news-sources/{id}/crawl` (async queue in non-test env).
- E2E is marked `n/a` per this story's validation contract: browser proof was not required for RSS crawl/raw storage.
