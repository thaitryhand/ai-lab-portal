# US-036 News Source Registry

## Status

implemented

## Product Contract

Admins can list, create, enable/disable, and configure crawl sources (RSS, GitHub, website) for AI News.

## Validation

`scripts/bin/harness-cli story verify US-036` → `python -m pytest backend/tests/test_news_sources.py`

## Evidence

- `backend/app/news_sources.py`, migration `20260603_0013`
- Admin UI `/admin/news-sources`
- `backend/tests/test_news_sources.py` (2 tests)
- 2026-06-04 E2E closeout:
  - `frontend/tests/e2e/admin-proof-gaps.spec.ts` covers admin news source create/list UI.
  - `npm run test:e2e` → 10 passed.
