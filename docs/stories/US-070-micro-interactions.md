# US-070 Micro-interactions

## Status

planned

## Lane

tiny

## Intake

#94 — change_request

## Product Contract

User interactions should feel responsive with subtle animations: page transitions,
hover effects on cards and buttons, and toast improvements.

## Relevant Product Docs

None.

## Acceptance Criteria

1. Link/card hover effects: subtle scale or shadow on `PublicIndexEntry`, nav links.
2. Button hover transitions consistent across all buttons.
3. Toast notifications appear with slide-in animation (if using sonner/toast).
4. Page transitions (optional: simple fade on route change).

## Design Notes

- Use CSS `transition` properties, not heavy animation libraries.
- Focus on existing components: `PublicIndexEntry`, `buttonVariants`, `AdminModuleCard`.
- Minimal approach: 150-200ms transitions with ease-in-out.
- No disruptive animations — subtlety is key.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A (UI only). |
| Integration | Hover states and transitions render in browser. |
| E2E | N/A. |
| Platform | N/A. |
| Release | Frontend typecheck/lint/build. |

## Harness Delta

None expected.

## Evidence

To be filled after implementation.
