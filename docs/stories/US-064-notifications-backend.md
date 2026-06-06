# US-064 Notifications Backend

## Status

implemented

## Lane

normal

## Intake

#89 — new_initiative

## Product Contract

Users should receive notifications when someone follows them or replies to their
comments. Notifications are user-scoped and persist in the database.

## Relevant Product Docs

- `docs/product/overview.md`

## Acceptance Criteria

1. `notifications` table with: `id`, `user_id`, `type` (follow | comment_reply | mention), `actor_user_id`, `resource_id`, `resource_type`, `read`, `created_at`.
2. Notification auto-created when user is followed (in follow/unfollow flow).
3. Notification auto-created when someone replies to user's comment.
4. `GET /public/notifications` returns unread notifications for signed user (auth required).
5. `POST /public/notifications/{id}/read` marks single notification as read.
6. `POST /public/notifications/read-all` marks all as read.
7. `GET /public/notifications/unread-count` returns count of unread notifications.
8. Old notifications are auto-deleted after 90 days (optional cleanup job).

## Design Notes

- Table: `notifications` in `backend/app/database.py`.
- Create notification in follow service after follow event.
- Create notification in comment service after reply is approved.
- Only approved comments trigger notifications (not pending/rejected).
- API routes in new `backend/app/notifications.py` module.
- Follow existing patterns: user identity header for auth.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Backend tests for notification creation, list, mark-read, unread-count. |
| Integration | Follow event creates notification; comment reply creates notification. |
| E2E | N/A (no dedicated E2E for notification creation). |
| Platform | N/A. |
| Release | Backend tests; frontend typecheck/lint/build unaffected for backend-only. |

## Harness Delta

None expected.

## Evidence

To be filled after implementation.
