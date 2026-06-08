# US-102 AI Lab Tour — Navigation Integration & Hero

## Status

implemented

## Lane

normal

## Intake

#112 AI Lab Tour page — interactive 7-stage pipeline showcase (2026-06-08).

## Product Contract

The AI Lab Tour is connected to the main public site. The hero section on `/` was rewritten from "MVP 1 · Manual CMS" to a tagline that sells the AI pipeline ("From project to published — powered by AI, reviewed by humans" with a CTA to the Tour). The navigation header includes a green featured "Tour" pill that stands out from regular nav items. The Tour itself has a hero section (TourHero) with headline, subtitle, and CTA buttons.

## Acceptance Criteria

1. Home hero rewritten to sell the AI pipeline with a Tour CTA link.
2. Navigation includes "Tour" as a featured green pill item.
3. TourHero component has headline, subtitle, and two CTA buttons.
4. Navigation `NavItem` type supports optional `featured` boolean prop.
5. Responsive hero renders correctly on mobile and desktop.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | 3/3 tests for NavItem type utilities |
| Integration | N/A |
| E2E | Manual: "Tour" pill visible in nav, hero CTA links to /tour |
| Platform | Frontend typecheck passes |
| Release | Navigable flow from landing page → tour |

## Evidence

- `frontend/components/public/public-home-hero.tsx` — Rewritten hero with pipeline tagline
- `frontend/components/public/public-landing-header.tsx` — Tour pill in nav
- `frontend/components/tour/tour-hero.tsx` — Tour page hero
- `frontend/app/page.tsx` — Hero section uses updated component
