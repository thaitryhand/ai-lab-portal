# Blog Tags — Implementation Plan

## Goal

Add a normalized **blog tags** model so admins can attach tags to posts, public readers can see tag chips and filter the blog index by tag, and the admin editor supports multi-select tag assignment.

Aligns with `docs/product/blog-agent.md` MVP acceptance (“Blog posts support tags”) and deferred item in `docs/product/mvp-roadmap.md` (full tags model).

## Lane

**Normal** — bounded to blog CMS + public read model; no auth model changes.

## Conventions (must follow)

| Area | Pattern to mirror |
| --- | --- |
| DB tables | `backend/app/database.py` + Alembic `backend/migrations/versions/` |
| Repository | `backend/app/blog_social.py` — ABC + `InMemory*` + `Postgres*` |
| Routes | `create_*_routes()` factory, `APIRouter`, signed admin/user headers |
| Public API | `/public/...` with `cache: no-store` on frontend |
| Admin API | `/admin/...` + `require_configured_admin_identity` |
| Frontend lib | `frontend/lib/blog/*.ts` — snake_case API → camelCase types |
| UI | `components/blog/*`, `components/public/*`, shadcn + existing admin form primitives |
| Tests | `backend/tests/test_*.py` unit/integration; optional Playwright slice |

## Data model

### Tables

```sql
blog_tags (
  id          VARCHAR(64)  PK,
  slug        VARCHAR(80)  UNIQUE NOT NULL,  -- ^[a-z0-9]+(?:-[a-z0-9]+)*$
  name        VARCHAR(120) NOT NULL,         -- display label
  created_at  TIMESTAMPTZ  NOT NULL
)

blog_post_tags (
  post_id  VARCHAR(64)  FK -> blog_posts.id ON DELETE CASCADE,
  tag_id   VARCHAR(64)  FK -> blog_tags.id ON DELETE CASCADE,
  PRIMARY KEY (post_id, tag_id)
)
```

Indexes:

- `ix_blog_post_tags_tag_id` on `tag_id` (filter posts by tag)
- `ix_blog_post_tags_post_id` on `post_id` (load tags for post)

### Pydantic models (`backend/app/blog_tags.py`)

- `BlogTag` — `id`, `slug`, `name`, `created_at`
- `BlogTagCreate` — `name` (slug auto-slugified server-side) or explicit `slug`
- `BlogTagSummary` — `slug`, `name`, `post_count` (public list)
- Extend `BlogPostSummary` / `BlogPostDetail` / `AdminBlogPostDetail` with `tags: list[BlogTagSummary]` (or `list[str]` slugs on summary, full objects on detail — prefer **slug + name** on public surfaces)

## Migration

- File: `backend/migrations/versions/20260604_0026_blog_tags.py`
- `down_revision`: `20260604_0025`
- Mirror style of `20260604_0025_blog_social_features.py`
- Register tables in `backend/app/database.py` (`blog_tags`, `blog_post_tags`)
- Update `backend/tests/test_migrations.py` if it asserts head revision name

## Backend

### New module: `backend/app/blog_tags.py`

**Repository protocol `BlogTagRepository`:**

| Method | Purpose |
| --- | --- |
| `list_tags()` | All tags with published-post counts (optional: all posts for admin) |
| `get_tag_by_slug(slug)` | Single tag |
| `create_tag(request)` | Admin create; slug unique |
| `set_post_tags(post_id, tag_ids)` | Replace junction rows for a post |
| `get_tags_for_post(post_id)` | Tags for one post |
| `get_post_ids_for_tag_slug(slug)` | Filter helper |
| `delete_tag(tag_id)` | Optional admin; only if no posts or cascade junction |

Implement `InMemoryBlogTagRepository` and `PostgresBlogTagRepository(engine)` like `blog_social.py`.

**Slug rules:** reuse blog slug regex; normalize `name` → slug via same rules as `slugify()` in `blog-editor.tsx` (lowercase, hyphens, max 80).

### Extend `backend/app/blog.py`

- `PostgresBlogRepository.list_published(tag_slug: str | None = None)` — when `tag_slug` set, join `blog_post_tags` + `blog_tags`, filter published only
- `get_published_by_slug` — eager-load tags into `BlogPostDetail`
- Do **not** embed tag IDs in `BlogPostCreate`/`BlogPostUpdate`; keep tag writes in tag repository + admin route (clearer boundary, matches social features split)

### Routes

**New:** `create_blog_tag_routes(tag_repo, blog_repo, settings) -> APIRouter`

| Method | Path | Auth | Behavior |
| --- | --- | --- | --- |
| GET | `/public/blog-tags` | none | `[{ slug, name, post_count }]` — count **published** posts only |
| GET | `/public/blog-posts` | none | Add optional query `?tag=<slug>` (extend existing handler in `main.py` or delegate to repo) |
| GET | `/public/blog-posts/{slug}` | none | Include `tags` on detail (already returns `BlogPostDetail`) |

**New:** `create_blog_tag_admin_routes(tag_repo, blog_repo, settings) -> APIRouter`

| Method | Path | Auth | Behavior |
| --- | --- | --- | --- |
| GET | `/admin/blog-tags` | admin | All tags + counts (draft + published) |
| POST | `/admin/blog-tags` | admin | Create tag |
| PUT | `/admin/blog-posts/{post_id}/tags` | admin | Body: `{ "tag_ids": string[] }` — replace associations |
| DELETE | `/admin/blog-tags/{tag_id}` | admin | Optional; 409 if tag in use unless product wants force |

Wire in `backend/app/main.py`:

```python
app.include_router(create_blog_tag_routes(...))
app.include_router(create_blog_tag_admin_routes(...))
```

### App factory / DI

In `create_app()`, instantiate `PostgresBlogTagRepository(engine)` when DB mode, else in-memory for tests — same pattern as `social_repo`.

## Frontend

### Lib: `frontend/lib/blog/tags.ts`

- `listPublicTags()`, `listPublishedBlogPosts({ tag?: string })`, extend `getPublishedBlogPost` type with `tags`
- Admin: `listAdminTags(session)`, `createTag(session, name)`, `setPostTags(session, postId, tagIds)`

### Components

| Component | Location | Role |
| --- | --- | --- |
| `BlogTagChips` | `components/blog/blog-tag-chips.tsx` | Linked chips → `/blog?tag=<slug>` |
| `BlogTagFilter` | `components/blog/blog-tag-filter.tsx` | Client or server wrapper: dropdown/tabs on index |
| `AdminTagMultiSelect` | `components/admin/admin-tag-multi-select.tsx` | Combobox multi-select; loads admin tags |

### Pages

1. **`app/blog/page.tsx`**
   - Read `searchParams.tag`
   - Pass `tag` to `listPublishedBlogPosts({ tag })`
   - Render `BlogTagFilter` + active tag label
   - Show chips on each `PublicIndexEntry` (optional compact row)

2. **`app/blog/[slug]/page.tsx`**
   - Render `BlogTagChips` under article header

3. **`components/admin/blog-editor.tsx`**
   - Load tags when `initialPostId` present
   - `AdminTagMultiSelect` — on save/publish, call `setPostTags` after post save (same pattern as draft save → second API call)

4. **`app/admin/blog/[id]/edit/page.tsx`** (if exists) — ensure tags loaded on edit route

### Server actions

Extend `app/admin/blog/editor/actions.ts` or add `tags/actions.ts`:

- After successful `saveDraft` / before `publish`, `PUT /admin/blog-posts/{id}/tags` with selected IDs

## Tests

### Backend (`backend/tests/test_blog_tags.py`)

- Create tag, duplicate slug → 409
- Attach tags to post, list published filtered by tag
- Public tag list post_count respects publish status
- Unpublish removes post from tag filter counts
- Migration head includes `blog_tags`

### Frontend

- Unit: slug/display mapping in `tags.ts` (optional)
- E2E (stretch): admin assigns tag → public index filter shows post — follow `tests/e2e/shell.spec.ts` patterns

## Verification commands

```bash
python -m alembic -c backend/alembic.ini upgrade head
uv run pytest backend/tests/test_blog_tags.py -q
cd frontend && npm run lint && npm run typecheck
# optional
cd frontend && npx playwright test tests/e2e/shell.spec.ts -g blog
```

## Harness / story follow-up

After implementation:

1. Add story `docs/stories/epics/E02-manual-cms/US-0XX-blog-tags.md` from `docs/templates/story.md`
2. `scripts/bin/harness-cli story add` + update proof flags
3. Update `docs/product/mvp-roadmap.md` — move “Full tags model” to implemented
4. Trace via `scripts/bin/harness-cli trace`

## File checklist

| Action | Path |
| --- | --- |
| Add | `backend/app/blog_tags.py` |
| Edit | `backend/app/database.py` |
| Edit | `backend/app/blog.py` (tag filter + detail tags) |
| Edit | `backend/app/main.py` |
| Add | `backend/migrations/versions/20260604_0026_blog_tags.py` |
| Add | `backend/tests/test_blog_tags.py` |
| Add | `frontend/lib/blog/tags.ts` |
| Edit | `frontend/lib/blog/posts.ts` |
| Add | `frontend/components/blog/blog-tag-chips.tsx` |
| Add | `frontend/components/blog/blog-tag-filter.tsx` |
| Add | `frontend/components/admin/admin-tag-multi-select.tsx` |
| Edit | `frontend/app/blog/page.tsx` |
| Edit | `frontend/app/blog/[slug]/page.tsx` |
| Edit | `frontend/components/admin/blog-editor.tsx` |
| Edit | `frontend/app/admin/blog/editor/actions.ts` |

## Out of scope (this slice)

- Tag hierarchies / categories tree
- Auto-suggest tags from AI blog agent
- RSS per-tag feeds
- Tag moderation workflow

## Risk notes

- **Low:** additive tables, no change to publish/auth boundaries
- Ensure `?tag=` on `/public/blog-posts` does not break existing clients (optional param only)
