# US-105 Related Article Recommendations

## Status

planned

## Lane

normal

## Intake

#115 — Content Analytics & Insights

## Product Contract

Add related article recommendations to the public blog detail page (`/blog/[slug]`). Uses tag overlap, category matching, and view popularity to suggest 3-5 related posts at the bottom of each article.

## Epic

E15-content-analytics

## Affected Docs

- `backend/app/blog_posts.py` — add `get_related_posts(repository, post_id, limit=5)` query
- `frontend/app/blog/[slug]/page.tsx` — add "Related Articles" section
- `frontend/components/blog/related-posts.tsx` — new component

## Acceptance Criteria

1. At bottom of each blog post, show "Related Articles" heading with 3-5 article cards
2. Articles are selected by: tag overlap (primary), category match (secondary), view count tiebreaker
3. Currently viewed article is excluded
4. Each card shows: title, excerpt (first 120 chars), reading time, publish date
5. Empty state: if no related articles found, section is not rendered
6. Clicking a card navigates to `/blog/[slug]` of that article
7. Responsive grid: 3 columns desktop, 2 tablet, 1 mobile
8. Frontend typecheck, lint, and build pass

## Non-Goals

- No ML-based recommendations (tag/category overlap only)
- No personalization per user
- No caching layer (simple SQL query per page load)

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `get_related_posts` returns correct posts excluding current |
| Integration | Backend tests pass |
| E2E | Visual check: related articles appear below seeded blog post |
| Platform | N/A |
| Release | `cd frontend && npm run typecheck && npm run lint && npm run build` |
