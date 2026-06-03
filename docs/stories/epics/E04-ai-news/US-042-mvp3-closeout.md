# US-042 MVP3 AI News Closeout

## Status

implemented

## Lane

tiny

## Product Contract

Close MVP 3 (AI News from official sources) with updated roadmap status, product
docs, and a combined verification command covering US-036–US-041.

## Acceptance Criteria

- `docs/product/mvp-roadmap.md` marks MVP 3 **Implemented** (US-036–US-041).
- `docs/product/news-intelligence.md` records shipped scope and deferred items.
- Combined news pipeline tests pass.
- Harness story verify passes.

## Validation

```bash
python -m pytest backend/tests/test_news_sources.py backend/tests/test_news_crawl.py backend/tests/test_news_extraction.py backend/tests/test_news_dedup.py backend/tests/test_news_scoring.py backend/tests/test_news_publish.py
scripts/bin/harness-cli story verify US-042
```

## Evidence

- 2026-06-03: combined news pytest → 23 passed.
- 2026-06-03: `scripts/bin/harness-cli story verify US-042` → pass.

## Deferred (post-MVP3)

- Public topic filtering on `/ai-news`.
- LLM-based scoring prompts (MVP uses heuristic scorer).
- GitHub/website source types beyond RSS crawl path.
- Dedicated admin review-queue UI (API-only for now).
