# US-038 Article Extraction From Raw News Items

## Status

implemented

## Lane

normal

## Product Contract

Linked URLs from `news_raw_items` are extracted asynchronously in workers (never inline
on public requests). Results land in `news_extracted_articles` with markdown/text,
provider metadata, and success/failure status. Firecrawl is used when
`AI_LAB_FIRECRAWL_API_KEY` is set; otherwise the fake extractor runs (tests/dev).

## Acceptance Criteria

- Migration adds `news_extracted_articles` keyed by `raw_item_id` (unique).
- Celery `news.extract_raw_item` and `news.extract_pending_raw_items`.
- Admin `POST /admin/news-sources/raw-items/{id}/extract` queues or runs sync (test).
- Admin `GET` list raw items per source and get extraction by raw item id.
- SSRF validation reuses `validate_fetch_url` before provider fetch.
- Tests use `FakeArticleExtractor` without network.

## Validation

```bash
python -m pytest backend/tests/test_news_extraction.py
scripts/bin/harness-cli story verify US-038
```

## Evidence

- 2026-06-03: `python -m pytest backend/tests/test_news_extraction.py` → 3 passed.
