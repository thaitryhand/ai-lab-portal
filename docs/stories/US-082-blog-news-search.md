# US-082 Blog and AI News Search

## Status

implemented

## Lane

normal

## Intake

Retroactive — harness hygiene sync (2026-06-06).

## Product Contract

Users should be able to search published blog posts and AI news items by
keyword. Search uses repository-level ILIKE filtering with sane limits.

## Acceptance Criteria

1. Blog repository supports case-insensitive keyword search on title/excerpt/content.
2. News repository supports case-insensitive keyword search on relevant fields.
3. Public or admin UI exposes search where designed (blog list, news list).
4. Search returns empty results gracefully without error.
5. Backend tests cover search filter behavior.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Repository search unit tests |
| Integration | API search query tests |
| E2E | Search smoke where UI exposed |
| Platform | N/A |
| Release | `python -m pytest` targeted search tests |

## Evidence

- Commit `79c4946` — feat(search): implement ILIKE filtering in blog and news repositories
