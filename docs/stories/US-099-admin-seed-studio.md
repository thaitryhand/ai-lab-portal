# US-099 Admin Seed Studio — Content Seeding UI

## Status

implemented

## Lane

normal

## Intake

#113 Admin Seed Studio — Content Seeding UI for demo population (2026-06-08).

## Product Contract

Admin Seed Studio provides a beautiful idempotent content seeding interface at `/admin/seed-studio`. A single POST `/admin/seed/all` endpoint seeds blog posts, showcases, projects, and tags into the database. The UI shows per-type cards with descriptions, seeded counts, and a feedback loop. The endpoint is idempotent — running it multiple times does not create duplicates. A Seed Studio module card appears on the admin operations dashboard.

## Acceptance Criteria

1. `POST /admin/seed/all` seeds 3 blog posts, 3 showcases, 2 projects, 8 tags.
2. Endpoint is idempotent (skips existing slugs).
3. Seed Studio page at `/admin/seed-studio` with content-type cards.
4. "Seed all content" button with loading spinner and success/error feedback.
5. Seed Studio module card listed on `/admin` operations dashboard.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A |
| Integration | N/A |
| E2E | Manual: POST /admin/seed/all returns correct counts; UI renders correctly |
| Platform | Python backend typecheck, frontend typecheck pass |
| Release | Full backend suite passes |

## Evidence

- `backend/app/admin_seed.py` — Admin seed router with POST /admin/seed/all
- `frontend/app/admin/seed-studio/page.tsx` — Seed Studio admin page
- `frontend/app/admin/page.tsx` — Seed Studio module card added
- `backend/app/main.py` — Seed router registered
