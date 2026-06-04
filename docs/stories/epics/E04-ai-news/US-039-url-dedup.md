# US-039 URL Canonicalization and Exact Deduplication

## Status

implemented

## Lane

normal

## Product Contract

After successful article extraction, URLs are canonicalized (scheme/host/path/query
normalization, tracking params stripped) and stored on `news_extracted_articles`.
Exact URL matches and exact content-hash matches mark later rows as duplicates of the
earliest successful extraction.

## Acceptance Criteria

- Migration `20260603_0016` adds `canonical_url_normalized`, `duplicate_status`,
  `duplicate_of_id` with indexes on normalized URL and content hash.
- `canonicalize_url()` normalizes http(s) URLs for dedup keys.
- `apply_dedup()` runs after successful `run_extract_raw_item`.
- Duplicate statuses: `unique`, `url_duplicate`, `content_duplicate`.
- Unit tests in `backend/tests/test_news_dedup.py`.

## Validation

```bash
python -m pytest backend/tests/test_news_dedup.py backend/tests/test_news_extraction.py
scripts/bin/harness-cli story verify US-039
```

## Evidence

- 2026-06-03: `python -m pytest backend/tests/test_news_dedup.py` → 5 passed.
- 2026-06-03: `scripts/bin/harness-cli story verify US-039` → pass.
- E2E is marked `n/a`: canonicalization and exact deduplication are backend data-processing rules.
