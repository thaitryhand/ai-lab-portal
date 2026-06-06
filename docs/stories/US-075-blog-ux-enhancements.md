# US-075 Blog UX Enhancements

## Status

implemented

## Lane

normal

## Intake

Retroactive — harness hygiene sync (2026-06-06).

## Product Contract

The public blog should feel like a modern editorial product: reading time,
RSS feed, smoother pagination/infinite scroll, tag-aware related posts, and
polished list/detail navigation.

## Acceptance Criteria

1. Blog posts display estimated reading time.
2. RSS feed is available for published posts.
3. Blog list supports infinite scroll or real pagination (no fake page stubs).
4. Related posts respect shared tags.
5. Navigation between blog pages avoids double-flicker regressions.
6. Frontend typecheck, lint, build, and targeted E2E pass.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A |
| Integration | Backend blog read APIs remain passing |
| E2E | Blog list/detail smoke in Playwright |
| Platform | N/A |
| Release | Frontend quality gate |

## Evidence

- Commit `6e9de5c` — blog UX: reading time, RSS, infinite scroll, tags, related posts
- Commit `294748c` — blog: real pagination, QA smoke, tag-aware related posts
- Commit `5968060` — fix: eliminate double flicker on blog page navigation
