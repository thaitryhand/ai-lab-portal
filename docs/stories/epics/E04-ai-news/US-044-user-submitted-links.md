# US-044 User-Submitted AI News Links

## Status

implemented

## Lane

normal

## Product Contract

Public users can submit AI-related URLs at `/ai-news/submit`. Submissions are
SSRF-validated, canonicalized for idempotency, rate-limited, processed
asynchronously, and listed for admin review. Duplicate URLs against existing
extracted articles are flagged.

## Acceptance Criteria

- Migration `20260603_0019` adds `news_submitted_links`.
- `POST /public/submitted-links` with validation, idempotency, rate limit.
- Admin list/get/process under `/admin/news/submitted-links`.
- Celery `news.process_submitted_link`.
- Frontend `/ai-news/submit` form.
- Tests in `backend/tests/test_news_submitted_links.py`.

## Validation

```bash
python -m pytest backend/tests/test_news_submitted_links.py
scripts/bin/harness-cli story verify US-044
```

## Evidence

- 2026-06-03: `python -m pytest backend/tests/test_news_submitted_links.py` → 4 passed.
- 2026-06-03: `scripts/bin/harness-cli story verify US-044` → pass.
