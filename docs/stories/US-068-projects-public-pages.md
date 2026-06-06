# US-068 Projects Public Pages

## Status

implemented

## Lane

normal

## Intake

#92 — change_request

## Product Contract

Public visitors can browse published projects at `/projects` and view individual
project details at `/projects/[slug]`.

## Relevant Product Docs

- `docs/product/overview.md`

## Acceptance Criteria

1. `GET /projects` renders list of published projects using `PublicPageShell`.
2. `GET /projects/[slug]` renders full project detail page.
3. Public nav includes "Projects" link.
4. Empty state when no published projects exist.
5. SEO metadata for each project page.

## Design Notes

- Pattern follows Showcases public pages (`frontend/app/showcases/`).
- Use `PublicIndexList`, `PublicIndexEntry` for list view.
- Detail page renders markdown content.
- Navigation items updated.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A (UI only). |
| Integration | Page fetches and renders projects from public API. |
| E2E | N/A (covered by typecheck). |
| Platform | N/A. |
| Release | Frontend typecheck/lint/build. |

## Harness Delta

None expected.

## Evidence

To be filled after implementation.
