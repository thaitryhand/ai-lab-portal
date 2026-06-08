# US-101 AI Lab Tour — Stats Counter & Live Examples

## Status

implemented

## Lane

normal

## Intake

#112 AI Lab Tour page — interactive 7-stage pipeline showcase (2026-06-08).

## Product Contract

The AI Lab Tour page at `/tour` includes a Stats section with animated counters (blog posts, pages processed, AI runs, human reviews) and a Live Examples section showcasing real seeded content. Stats use framer-motion `useInView` for count-up animations on scroll. Examples render as 3×2 card grid with title, excerpt, and links to blog, showcases, and projects. Currently uses hardcoded demo data; ready for backend live-data integration.

## Acceptance Criteria

1. Stats section with 4 animated counters: blog posts, pages processed, AI runs, human reviews.
2. Counters animate up when scrolled into view.
3. Live Examples section with 6 cards in a 3×2 grid.
4. Cards show: title, excerpt, category badge, "Read more" link.
5. Responsive layout (2-column on desktop, 1-column on mobile).

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A |
| Integration | N/A |
| E2E | Manual: Stats animate on scroll, examples render with links |
| Platform | Frontend typecheck passes |
| Release | Content visible on `/tour` without backend |

## Evidence

- `frontend/components/tour/tour-stats.tsx` — Animated stats counter section
- `frontend/components/tour/tour-examples.tsx` — Live examples card grid
