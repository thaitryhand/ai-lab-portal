# US-072 Dashboard Stats API

## Status

planned

## Lane

normal

## Intake

#95 — change_request

## Product Contract

The admin dashboard needs a backend endpoint that returns aggregated counts
and recent activity for dashboard widgets.

## Relevant Product Docs

None — enhancement of existing admin dashboard.

## Acceptance Criteria

1. `GET /admin/dashboard/stats` returns JSON with: `blog_post_count`, `news_item_count`, `blog_idea_count`, `user_count`, `comment_count`, `contact_message_count`.
2. Response also includes `recent_activity` array of recent audit events (last 10).
3. Endpoint is auth-protected (admin only).
4. Cache-friendly: counts can be stale within a few seconds for MVP.

## Design Notes

- New route in `backend/app/main.py` or `backend/app/admin_dashboard.py`.
- Queries are simple `SELECT count(*)` on relevant tables.
- `recent_activity` from `audit_events` table.
- Separate concerns: don't mix stats logic into existing admin route.
- Pattern: return typed Pydantic response model.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Backend tests for stats endpoint with known data. |
| Integration | Endpoint returns correct counts for each entity. |
| E2E | N/A (admin API, covered by integration). |
| Platform | N/A. |
| Release | Backend tests; frontend typecheck/lint/build. |

## Harness Delta

None expected.

## Evidence

To be filled after implementation.
