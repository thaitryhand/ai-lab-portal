# US-065 Notifications UI

## Status

planned

## Lane

tiny

## Intake

#93 — change_request

## Product Contract

Authenticated users should see a notification bell icon in the navigation with
unread count badge, and a dropdown showing recent notifications.

## Relevant Product Docs

- `docs/product/overview.md`

## Acceptance Criteria

1. Bell icon in public navigation dropdown when user is signed in.
2. Bell icon shows unread count badge.
3. Clicking bell opens dropdown with recent notifications (actor name, type, time).
4. Clicking a notification marks it as read and navigates to relevant resource.
5. "Mark all read" action in dropdown.
6. Admin shell navigation also includes notification bell.

## Design Notes

- New component: `frontend/components/public/notification-bell.tsx`.
- Client component fetching from `/public/notifications/unread-count` and `/public/notifications`.
- Poll or interval for unread count (every 30s or on page focus).
- Dropdown uses shadcn Popover or similar.
- Follow existing auth pattern with `auth.api.getSession`.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A (UI only). |
| Integration | Component fetches and renders notifications from API. |
| E2E | N/A (requires auth + notification creation flow). |
| Platform | N/A. |
| Release | Frontend typecheck/lint/build. |

## Harness Delta

None expected.

## Evidence

To be filled after implementation.
