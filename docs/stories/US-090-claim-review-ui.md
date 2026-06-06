# US-090 Claim Review UI

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — claim gate UX for admin publish workflow (2026-06-06).

## Product Contract

Admin operators can review extracted claims with clear status, attach structured
evidence, waive individually or in bulk, mark unsupported, and see when claims
block publishing.

## Acceptance Criteria

1. Claim section shows summary counts (pending, supported, waived, unsupported).
2. Blocking banner when claims prevent publish; cleared banner when ready.
3. Pending claims expose evidence source select + reference field.
4. Actions: mark supported, waive, mark unsupported, waive all pending.
5. Publish button disabled while blocking claims remain; link to claims section.
6. Unit test for claim publish gate helper.
7. Frontend typecheck and build pass.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `claim-publish-gate.test.ts` |
| Integration | Existing claim PATCH API |
| E2E | US-086 golden path (waive for publish) |
| Platform | N/A |
| Release | Frontend quality gate |

## Evidence

- `frontend/app/admin/blog-ideas/claim-review-panel.tsx`
- `frontend/app/admin/blog-ideas/lib/claim-publish-gate.ts`
- `frontend/app/admin/blog-ideas/actions.ts` — `waiveAllClaimsAction`
