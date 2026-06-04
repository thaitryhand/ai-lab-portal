# US-049 LLM AI News Scoring

## Status

implemented

## Lane

normal

## Product Contract

AI News scoring can use a structured LLM output for score dimensions, summary, and why-it-matters copy while preserving the existing heuristic scoring path as a deterministic fallback.

## Relevant Product Docs

- `docs/product/news-intelligence.md`
- `docs/product/mvp-roadmap.md`

## Acceptance Criteria

- Prompt registry includes an AI News scoring prompt and version.
- Structured schema validates LLM scoring dimensions, summary, and why-it-matters.
- `run_score_extracted_article` accepts an optional LLM service and records LLM-derived scores when available.
- Scoring falls back to heuristic output when no LLM service is provided or LLM generation fails.
- Tests use fake LLM service only; no provider calls in tests.

## Design Notes

- Commands: existing scoring jobs.
- Queries: none.
- API: no public/admin API shape change.
- Tables: no migration; `scorer_version` records `llm_news_scoring:<prompt version>` or `heuristic_v1`.
- Domain rules: heuristic fallback remains required for local/dev/test resilience.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | LLM schema/prompt tests and targeted news scoring tests. |
| Integration | Existing backend scoring/publish tests pass. |
| E2E | Frontend build not required unless UI changes. |
| Platform | Not required. |
| Release | `harness-cli story verify US-049` passes. |

## Harness Delta

None expected.

## Evidence

- `python -m pytest backend/tests/test_llm.py backend/tests/test_news_scoring.py` — 27 passed.
- `python -m pytest backend/tests/test_news_publish.py backend/tests/test_news_submitted_links.py` — 9 passed.
- `cd frontend && npm run typecheck` — passed after aligning review UI status labels with backend `candidate` status.
- `cd frontend && npm run lint` — passed.
- `cd frontend && npm run build` — passed.
