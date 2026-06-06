# US-073 Dashboard Stat Cards UI

## Status

implemented

## Lane

tiny

## Intake

#97 — change_request

## Product Contract

The admin dashboard should display real-time stats: post count, news count, idea
count, user count, comment count, and recent activity list.

## Relevant Product Docs

None — enhancement of existing admin dashboard.

## Acceptance Criteria

1. Admin dashboard `/admin` fetches real data from `GET /admin/dashboard/stats`.
2. Stat cards render numerical counts with labels and icons.
3. "Recent activity" section shows last 10 audit events with timestamp + description.
4. Stat cards update on page refresh (no polling for MVP).
5. Loading state while stats fetch.
6. Empty state when no activity exists.

## Design Notes

- Extend existing `AdminDashboardStatGrid` component or create new one.
- Existing `fetchAdminDashboardStats` lib function already exists — update it.
- Pattern: server component fetches stats and passes to client component.
- Icons match existing module cards (FileText, Newspaper, etc.).

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A (UI only). |
| Integration | Dashboard renders stats from API. |
| E2E | N/A (admin flow, covered by typecheck). |
| Platform | N/A. |
| Release | Frontend typecheck/lint/build. |

## Harness Delta

None expected.

## Evidence

To be filled after implementation.
