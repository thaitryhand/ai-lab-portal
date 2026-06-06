# US-069 Loading States

## Status

implemented

## Lane

tiny

## Intake

#98 — change_request

## Product Contract

Public pages should show loading skeletons while content fetches, improving
perceived performance and reducing layout shift.

## Relevant Product Docs

None.

## Acceptance Criteria

1. Blog list page shows skeleton cards while loading.
2. AI News list page shows skeleton cards while loading.
3. Project list page (once built) shows skeleton cards.
4. Profile page shows skeleton for user info and tabs.
5. Admin pages show loading state (at minimum a spinner).

## Design Notes

- Create `frontend/components/public/skeleton-card.tsx` - placeholder card matching `PublicIndexEntry` dimensions.
- Use shadcn `Skeleton` primitive or simple CSS shimmer.
- Next.js `loading.tsx` files for route-level loading boundaries where applicable.
- Avoid flash of loading on fast connections.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A (UI only). |
| Integration | Skeleton renders correctly when data is delayed. |
| E2E | N/A. |
| Platform | N/A. |
| Release | Frontend typecheck/lint/build. |

## Harness Delta

None expected.

## Evidence

To be filled after implementation.
