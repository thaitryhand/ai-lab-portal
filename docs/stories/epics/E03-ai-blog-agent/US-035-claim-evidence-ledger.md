# US-035 Claim Evidence Ledger

## Status

implemented

## Product Contract

Admins extract claims from approved drafts, attach evidence or waive items, and publishing is blocked while claims remain `pending` or `unsupported`.

## Validation

`scripts/bin/harness-cli story verify US-035` → `python -m pytest backend/tests/test_blog_observability.py -k claim`

## Evidence

- `backend/app/blog_claims.py`, publish validation in `blog_publish.py`
- Admin claims section in `idea-detail-view.tsx`
- `backend/tests/test_blog_observability.py` (publish guard + extract claims)
- 2026-06-04 E2E closeout:
  - `frontend/tests/e2e/admin-proof-gaps.spec.ts` covers claim extraction and claim evidence controls on the admin blog idea detail page.
  - `npm run test:e2e` → 10 passed.
