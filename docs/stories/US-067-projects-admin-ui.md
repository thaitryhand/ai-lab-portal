# US-067 Projects Admin UI

## Status

planned

## Lane

normal

## Intake

#91 — change_request

## Product Contract

Admin users can manage projects through the admin dashboard, following the same
pattern as Showcases.

## Relevant Product Docs

- `docs/product/overview.md`

## Acceptance Criteria

1. `AdminModuleCard` for Projects in admin dashboard, linking to `/admin/projects`.
2. `/admin/projects` lists all projects with status, title, published_at.
3. `/admin/projects/editor` for creating new projects (reuses BlogEditor-like pattern).
4. `/admin/projects/{id}/edit` for editing existing projects.
5. Project editor includes: title, description, image URL, content markdown.
6. Publish/unpublish actions on project detail page.
7. Admin nav updated with "Projects" link in sidebar.

## Design Notes

- Pattern follows Showcases admin UI closely.
- Reuse `BlogEditor` component or create a simpler `ProjectEditor`.
- Table columns: title, status, published_at, actions (edit, publish/unpublish).
- Admin auth required for all routes.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A (UI only). |
| Integration | Admin routes connect to backend CRUD correctly. |
| E2E | N/A (manual admin flow, covered by typecheck). |
| Platform | N/A. |
| Release | Frontend typecheck/lint/build. |

## Harness Delta

None expected.

## Evidence

To be filled after implementation.
