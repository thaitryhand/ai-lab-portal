# US-071 Responsive Polish

## Status

planned

## Lane

tiny

## Intake

#96 — change_request

## Product Contract

All public and admin pages render correctly on mobile viewports with proper
scrolling, readable text, and accessible tap targets.

## Relevant Product Docs

None.

## Acceptance Criteria

1. Mobile navigation: hamburger menu or collapsible nav on small screens.
2. Blog/news list cards stack vertically on mobile (no horizontal overflow).
3. Admin tables scroll horizontally on small screens.
4. Admin forms (editor, settings) have full-width inputs on mobile.
5. Public hero section text is readable on mobile (no overflow).
6. Touch targets are at least 44x44px per WCAG.

## Design Notes

- Mobile-first review of existing pages.
- Use Tailwind breakpoints: `sm:`, `md:`, `lg:`.
- Admin tables: wrap in horizontal scroll container.
- Nav: check existing mobile behavior, enhance if needed.
- Test at 375px width (mobile).

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A (UI only). |
| Integration | Pages render without overflow on mobile viewport. |
| E2E | N/A. |
| Platform | N/A. |
| Release | Frontend typecheck/lint/build; visual check at 375px. |

## Harness Delta

None expected.

## Evidence

To be filled after implementation.
