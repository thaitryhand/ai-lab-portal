# US-050 AI News Enhancement Closeout

## Status

implemented

## Lane

normal

## Product Contract

The post-MVP AI News enhancement batch is internally consistent and verified across public filtering, admin review, and LLM scoring slices.

## Relevant Product Docs

- `docs/product/news-intelligence.md`
- `docs/product/mvp-roadmap.md`

## Acceptance Criteria

- Combined diff for US-047, US-048, and US-049 is reviewed.
- Public topic filtering, admin review UI, and LLM scoring story records are implemented in the Harness matrix.
- Aggregate backend AI News/LLM validation passes.
- Aggregate frontend typecheck/lint/build passes.
- Whitespace diff check passes.

## Design Notes

- Commands: none.
- Queries: Harness matrix review.
- API: no additional API changes in this closeout.
- Tables: no migrations.
- UI surfaces: no additional UI changes in this closeout.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Backend LLM/news test bundle. |
| Integration | Backend public/review/submitted/crawl/extract/dedup tests. |
| E2E | Frontend typecheck/lint/build and route discovery. |
| Platform | Not required. |
| Release | `git diff --check` clean. |

## Harness Delta

No new friction recorded. During closeout, `git diff --check` found CRLF/trailing-whitespace noise in `backend/app/news_scoring.py`; the file was normalized to LF and validation was rerun. This was caused by an edit-script newline default, not a new Harness backlog item.

## Evidence

- `srcwalk review` — reviewed combined working tree evidence.
- `git diff --check` — initially failed on `backend/app/news_scoring.py`; passed after LF normalization.
- `python -m pytest backend/tests/test_llm.py backend/tests/test_news_scoring.py backend/tests/test_news_publish.py backend/tests/test_news_submitted_links.py backend/tests/test_news_crawl.py backend/tests/test_news_extraction.py backend/tests/test_news_dedup.py` — 50 passed after normalization.
- `cd frontend && npm run typecheck && npm run lint && npm run build` — passed after normalization.
