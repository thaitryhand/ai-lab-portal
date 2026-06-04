# US-063 Contact Page Frontend

## Status

planned

## Lane

normal

## Intake

#87 — change_request

## Product Contract

The public website must have a `/contact` page with a form that visitors can
use to send messages to the AI Lab team.

## Relevant Product Docs

- `docs/product/overview.md` — `/contact` listed as primary public surface

## Acceptance Criteria

1. `GET /contact` renders a contact form with fields: name, email, subject, message.
2. Form includes client-side validation (required fields, email format).
3. On successful submit, the form shows a confirmation/success state.
4. On error, the form shows an appropriate error message.
5. The page uses `PublicPageShell` for consistent layout.
6. Navigation includes a "Contact" link in the public nav.
7. Project `nav-items.ts` updated to include `/contact`.

## Design Notes

- Form submits to `POST /public/contact` (backend from US-062).
- Simple server action or direct fetch to backend.
- Consistent with existing public page styling (shadcn inputs).
- Success state can be an inline message or a separate thank-you page.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A (UI only). |
| Integration | Form submit reaches backend correctly. |
| E2E | N/A (manual flow covered by typecheck). |
| Platform | N/A. |
| Release | Frontend typecheck/lint/build. |

## Harness Delta

None expected.

## Evidence

To be filled after implementation.
