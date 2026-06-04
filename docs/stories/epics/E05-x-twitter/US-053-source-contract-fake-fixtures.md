# US-053 X/Twitter Source Contract and Fake Fixtures

## Status

implemented

## Lane

normal

## Product Contract

Define a normalized X/Twitter social post boundary and deterministic fake provider fixtures before any real Apify, Firecrawl, or X/Twitter provider call is allowed.

## Relevant Product Docs

- `docs/stories/epics/E05-x-twitter/README.md`
- `docs/decisions/0008-x-twitter-provider-strategy.md`
- `docs/product/news-intelligence.md`

## Acceptance Criteria

- A normalized social post contract captures provider, source scope, post text, URL, author metadata, timestamps, engagement metrics, quote/reply context, link entities, media URLs, and raw provider payload.
- Apify Xquik-like fake rows can be mapped into the normalized contract.
- Fake provider returns deterministic normalized posts without real provider calls.
- Invalid provider rows fail at the boundary.
- Tests prove the contract, fake fixture mapping, quote context, and URL validation.

## Design Notes

- Commands: none.
- Queries: none.
- API: no public/admin API change.
- Tables: no migration.
- Domain rules: social provider output remains untrusted; normalized contract is the parse-first boundary before AI filtering or ingestion.
- UI surfaces: none.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `python -m pytest backend/tests/test_social_x.py` |
| Integration | Run related AI News tests before closeout/commit. |
| E2E | Not required; no frontend change. |
| Platform | Not required. |
| Release | `git diff --check` clean. |

## Harness Delta

None.

## Evidence

- `python -m pytest backend/tests/test_social_x.py` — 7 passed.
