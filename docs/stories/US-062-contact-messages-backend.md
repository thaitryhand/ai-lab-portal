# US-062 Contact Messages Backend

## Status

implemented

## Lane

normal

## Intake

#88 — change_request

## Product Contract

The public `/contact` page needs a backend endpoint to accept and store
contact form submissions. Admin users must be able to view submitted messages.

## Relevant Product Docs

- `docs/product/overview.md` — `/contact` listed as primary public surface

## Acceptance Criteria

1. `contact_messages` table with: `id`, `name`, `email`, `subject`, `message`, `created_at`, `read_at`.
2. `POST /public/contact` accepts `{ name, email, subject, message }`, validates inputs, stores in DB.
3. Admin API `GET /admin/contact-messages` returns list of all messages (auth-protected).
4. Admin API `GET /admin/contact-messages/{id}` returns single message detail.
5. Admin API `PATCH /admin/contact-messages/{id}/read` marks message as read.

## Design Notes

- Table: `contact_messages` in `backend/app/database.py`.
- Public endpoint does NOT require auth.
- Admin endpoints behind `require_configured_admin_identity`.
- Input validation: name required (1-200 chars), email valid format, subject required (1-500 chars), message required (1-10000 chars).
- Rate limiting is optional for MVP.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Backend tests for public submit, validation errors, admin list/read. |
| Integration | Public endpoint stores and returns correct data. |
| E2E | N/A (no browser flow for admin-only feature). |
| Platform | N/A. |
| Release | Backend tests; frontend typecheck unaffected. |

## Harness Delta

None expected.

## Evidence

To be filled after implementation.
