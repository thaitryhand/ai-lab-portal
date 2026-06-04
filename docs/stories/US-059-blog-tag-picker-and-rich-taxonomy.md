# US-059 Blog Tag Picker and Rich Taxonomy

## Status

implemented

## Lane

normal

## Product Contract

Admins and public writers can assign rich blog tags using a tag picker during blog creation/editing, instead of typing a raw comma-separated field. The tag taxonomy should support many common developer tags (for example `ai`, `javascript`, `typescript`, `nodejs`, `programming`, `webdev`, `react`, `nextjs`, `python`, `agents`, `llm`, `openai`, `tools`) and remain extensible.

Public readers can click a tag chip and filter the blog index by that tag.

## Relevant Product Docs

- `docs/product/blog-agent.md`
- `docs/product/mvp-roadmap.md`
- `docs/plans/blog-tags-implementation.md`

## Current State

Implemented:

- `blog_tags` and `blog_post_tags` tables.
- Public tag filter: `/blog?tag=<slug>`.
- Public API: `/public/blog-tags`, `/public/blog-posts?tag=...`, `/public/blog-posts/{slug}/tags`.
- Admin API: `/admin/blog-tags`, `/admin/blog-posts/{post_id}/tags`.
- `BlogEditor` has `tagNames` input, but it is plain comma-separated text.

Gap:

- No dev.to-style picker/combobox.
- No seeded/default tag taxonomy.
- No quick-create tag UX inside the editor.
- No tag autocomplete or popular tags display.

## Acceptance Criteria

- Blog create/edit screen exposes a tag picker with:
  - searchable suggestions;
  - selected tag chips;
  - ability to create a new tag if no exact match exists;
  - max tag count per post (default: 4, matching dev.to-like behavior unless product chooses otherwise).
- Initial taxonomy includes a broad set of developer/AI tags, including at least:
  - `ai`, `javascript`, `typescript`, `nodejs`, `programming`, `webdev`, `react`, `nextjs`, `python`, `agents`, `llm`, `openai`, `tools`.
- Saving/publishing a post persists selected tags via existing admin tag API.
- Editing a post preloads selected tags.
- Public blog detail renders tag chips.
- Clicking a tag filters `/blog` by tag and shows active filter state.
- Existing raw comma input is removed or hidden behind a fallback only if picker fails.

## Design Notes

- Commands:
  - Admin save/publish actions continue to call `/admin/blog-posts`, then `/admin/blog-posts/{post_id}/tags`.
- Queries:
  - Use `GET /admin/blog-tags` to load options.
  - Use `GET /admin/blog-posts/{post_id}/tags` for edit preload.
- API:
  - Keep existing tag API unless picker needs a dedicated `POST /admin/blog-tags/ensure` endpoint.
- Tables:
  - Existing `blog_tags`, `blog_post_tags` remain sufficient.
- Domain rules:
  - Slug is normalized server-side.
  - Duplicate names resolve to existing tags where possible.
  - Tag names display as plain text; public chips render `#<name>`.
- UI surfaces:
  - `frontend/components/admin/blog-editor.tsx`
  - New `frontend/components/admin/admin-tag-picker.tsx`

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Backend tests for seed/default tags and duplicate normalization. |
| Integration | Editor action saves selected tags, edit route preloads selected tags. |
| E2E | E2E test: admin selects tag in editor, tag renders on public detail, tag filter works. |
| Platform | n/a unless deployed. |
| Release | Frontend typecheck/lint/build; backend tag tests. |

## Harness Delta

None expected.

## Evidence

Implemented in code:

- `backend/app/blog_tags.py` now seeds a rich default taxonomy and keeps missing defaults backfilled.
- `backend/migrations/versions/20260604_0026_blog_tags.py` creates `blog_tags` / `blog_post_tags` and inserts default tags.
- `frontend/components/admin/blog-editor.tsx` now uses a searchable tag picker with selected chips, create-new affordance, and max 4 tags.
- Blog create/edit routes pass available tags into `BlogEditor`.

Validation run:

```text
python -m pytest backend/tests/test_blog_tags.py -q
# 5 passed

python -m pytest backend/tests/test_blog_tags.py backend/tests/test_blog_public.py backend/tests/test_admin_blog.py -q
# 14 passed

cd frontend && npm run typecheck
# passed

cd frontend && npm run lint
# passed

cd frontend && npm run build
# passed; routes include /blog, /blog/[slug], /blog/new, /blog/edit/[id]
```

