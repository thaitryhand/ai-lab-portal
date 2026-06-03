# US-040 Heuristic Scoring and Review Queue

## Status

implemented

## Product Contract

Unique successful extractions receive heuristic multi-dimension scores and a
`news_review_items` row. Items meeting the review threshold enter the admin
candidate queue. Editors approve or reject candidates before public publish (US-041).

## Acceptance Criteria

- Migration `20260603_0017` adds `news_review_items`.
- `compute_heuristic_scores()` derives credibility, relevance, novelty, technical
  depth, business value, spam risk, and final publish score.
- Scoring runs after dedup on successful unique extractions when repos are wired.
- Celery `news.score_extracted_article` and `news.score_pending_extractions`.
- Admin APIs under `/admin/news/review-items` (list, get, approve, reject, rescore).
- Tests in `backend/tests/test_news_scoring.py`.

## Validation

```bash
python -m pytest backend/tests/test_news_scoring.py
scripts/bin/harness-cli story verify US-040
```

## Evidence

- 2026-06-03: `python -m pytest backend/tests/test_news_scoring.py` → 4 passed.
- 2026-06-03: `scripts/bin/harness-cli story verify US-040` → pass.
