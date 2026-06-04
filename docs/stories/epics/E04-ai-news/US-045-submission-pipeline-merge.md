# US-045 Submission Pipeline Merge

## Status

implemented

## Product Contract

Processing a submitted link materializes a raw item under the user-submissions
source, runs extract → dedup → score, and links the submission to the review
queue when eligible.

## Acceptance Criteria

- Migration `20260603_0020` adds `raw_item_id` and `review_item_id` on submissions.
- `run_process_submitted_link` creates raw item and runs extraction/scoring pipeline.
- Submission status `in_review` when a candidate review item is created.
- Default source `newssrc_user_submissions` (`user_submit` type).
- Tests cover pipeline integration in `backend/tests/test_news_submitted_links.py`.

## Validation

```bash
python -m pytest backend/tests/test_news_submitted_links.py
scripts/bin/harness-cli story verify US-045
```

## Evidence

- 2026-06-03: `python -m pytest backend/tests/test_news_submitted_links.py` → 5 passed.
- 2026-06-03: `scripts/bin/harness-cli story verify US-045` → pass.
- E2E is marked `n/a`: this story covers backend processing from submitted link to raw item, extraction, scoring, and review linkage.
