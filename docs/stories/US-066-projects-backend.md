# US-066 Projects Backend

## Status

planned

## Lane

normal

## Intake

#90 — new_initiative

## Product Contract

Projects are a CRUD entity similar to Showcases but for "company projects"
rather than client case studies. Admin users manage projects; public users
browse published projects.

## Relevant Product Docs

- `docs/product/overview.md`
- `docs/product/architecture.md`

## Acceptance Criteria

1. `projects` table with: `id`, `title`, `slug`, `description`, `content_markdown`, `image_url`, `status`, `published_at`, `created_at`, `updated_at`.
2. Admin CRUD API: `GET /admin/projects`, `GET /admin/projects/{id}`, `POST /admin/projects`, `PATCH /admin/projects/{id}`, `POST /admin/projects/{id}/publish`, `POST /admin/projects/{id}/unpublish`.
3. Public read API: `GET /public/projects` (published only, ordered by published_at), `GET /public/projects/{slug}` (published detail).
4. Audit events for project publish/unpublish actions.
5. Slug auto-generation from title with uniqueness check (follow blog pattern).

## Design Notes

- Pattern follows existing Showcases implementation (`backend/app/showcase.py`).
- Fields: title, slug, description (short), content_markdown (full), image_url, status, published_at, created_at, updated_at.
- Repository pattern: `ProjectRepositoryProtocol` + `PostgresProjectRepository` + in-memory for test.
- DB migration for `projects` table.
- Admin routes in `backend/app/main.py` or separate `backend/app/projects.py` module.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Backend tests for CRUD, publish/unpublish, slug uniqueness. |
| Integration | Public list filters to published only; admin auth enforced. |
| E2E | N/A (covered by existing E2E patterns). |
| Platform | N/A. |
| Release | Backend tests; frontend typecheck/lint/build. |

## Harness Delta

None expected.

## Evidence

To be filled after implementation.
