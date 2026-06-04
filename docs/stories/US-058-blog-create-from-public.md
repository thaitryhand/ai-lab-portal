# US-058 Blog Creation from Public Page

## Status

implemented

## Lane

normal

## Intake

#85 — change_request

## Product Contract

Add blog creation capability to the public blog page (`/blog`) by reusing the
existing Tiptap-based `BlogEditor` component and admin blog CRUD API. Allow
authenticated admin users to create and publish blog posts directly from the
public-facing blog section, without navigating to the admin dashboard.

## Affected Docs

- `frontend/app/blog/page.tsx`
- `frontend/app/blog/[slug]/page.tsx`
- `frontend/components/admin/blog-editor.tsx`
- Backend: `POST /admin/blog-posts` and `PATCH /admin/blog-posts/{id}` (existing)

## Acceptance Criteria

1. A "Write a post" call-to-action is visible on `/blog` for admin users only
   (non-admin visitors see no change).
2. Clicking "Write a post" navigates to `/blog/new` — a full-page editor view
   using the existing `BlogEditor` component wrapped in the public shell.
3. The editor supports: title, slug, excerpt, author name, and rich markdown
   content via Tiptap (all existing capabilities).
4. "Save draft" stores the post via `POST /admin/blog-posts` (existing API).
5. "Publish" publishes via `POST /admin/blog-posts/{id}/publish` (existing API).
6. After publish, the user is redirected to `/blog` where the new post appears.
7. The edit page at `/blog/[id]/edit` allows editing existing drafts/posts.
8. Non-admin users cannot see the "Write a post" button or access `/blog/new`.
9. Frontend typecheck, lint, and build pass.

## Non-Goals

- No new backend APIs. All CRUD operations use existing admin blog endpoints.
- No changes to the public blog reader experience.
- No AI-generated content features — this is pure manual blog creation.
- No image upload handling (Tiptap already supports links).

## Design Notes

- Layout: Full-page editor (Substack/Medium pattern) with top bar containing:
  status indicator, Save draft, and Publish buttons.
- The `BlogEditor` component is reused directly with the existing
  `saveDraftAction` and `publishAction` server actions.
- Wrapped in `PublicPageShell` for consistent public-facing look.
- Admin detection via `auth.api.getSession` in the server component.
- The `Write a post` button uses a Link component styled as a primary button.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A (UI change only, no new logic) |
| Integration | Backend tests remain passing |
| E2E | N/A (manual admin flow, covered by typecheck) |
| Platform | N/A |
| Release | `cd frontend && npm run typecheck && npm run lint && npm run build` |

## Harness Delta

- Created `frontend/app/blog/new/page.tsx` — new public blog editor route
- Created `frontend/app/blog/edit/[id]/page.tsx` — new edit route (uses `edit` static segment to avoid conflict with `[slug]`)
- Updated `frontend/app/blog/page.tsx` — added "Write a post" button for admin
- Updated E01 backlink for blog creation
- All existing blog routes, components, and API endpoints unchanged

## Evidence

- `cd frontend && npm run typecheck` — passed
- `cd frontend && npm run lint` — passed  
- `cd frontend && npm run build` — passed
- All existing backend tests remain passing
