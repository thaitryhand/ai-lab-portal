# User Profiles — Implementation Plan

## Goal

Add **full public user profiles** (display name, bio, avatar, links) stored in Postgres, auto-provisioned for each Better Auth user, editable at `/profile/edit`, viewable at `/profile` (own) and linked from comments.

User choice from intake: **Full profile** (name, bio, avatar, links) — not minimal auth-only fields.

## Lane

**Normal** — new table + user-scoped routes; touches comments display but not moderation rules.

## Conventions (must follow)

| Area | Pattern to mirror |
| --- | --- |
| User identity | `SignedIdentity` + `USER_IDENTITY_HEADER` / `USER_SIGNATURE_HEADER` (`admin_boundary.py`) |
| User-scoped API | `blog_social.py` `require_user_identity_with_settings` |
| Admin list | `create_blog_social_admin_routes` style `/admin/...` |
| Better Auth | `user` table (`id`, `name`, `email`, `image`) — **do not duplicate** email in profile; profile extends display |
| Frontend session | `auth.api.getSession`, `createUserBoundaryHeaders` (mirror admin boundary for user calls) |
| Comments | `blog_comments.user_name` + avatar circle in `blog-comments.tsx` |

## Data model

### Table `user_profiles`

```sql
user_profiles (
  user_id       TEXT  PK  FK -> "user".id ON DELETE CASCADE,
  display_name  VARCHAR(120)  NOT NULL,
  bio           TEXT  NULL,                    -- max 2000 chars at API
  avatar_url    VARCHAR(2048) NULL,
  website_url   VARCHAR(2048) NULL,
  github_url    VARCHAR(2048) NULL,
  linkedin_url  VARCHAR(2048) NULL,
  created_at    TIMESTAMPTZ NOT NULL,
  updated_at    TIMESTAMPTZ NOT NULL
)
```

**Design choice:** `user_id` is PK (1:1 with Better Auth `user`). No separate profile `id` — simplifies comments lookup.

**Defaults on create:**

- `display_name` ← `user.name` or local-part of email
- `avatar_url` ← `user.image` if set
- empty bio / links

### Pydantic (`backend/app/user_profiles.py`)

- `UserProfile` — full row
- `UserProfileUpdate` — optional fields, all validated (URL max length, bio max length)
- `UserProfilePublic` — safe subset for strangers: `user_id`, `display_name`, `bio`, `avatar_url`, `website_url`, `github_url`, `linkedin_url` (no email)
- `AdminUserProfileSummary` — adds `email` from join with `user` table for admin list

## Migration

- File: `backend/migrations/versions/20260604_0027_user_profiles.py`
- `down_revision`: `20260604_0026` (or `0025` if tags ship later — keep linear chain)
- Add table + FK to `"user"` (quoted identifier per Better Auth migration)

## Auto-create on signup

**Recommended: lazy `get_or_create` in repository** (minimal change, no Better Auth plugin required).

```python
def get_or_create(self, user_id: str, *, default_name: str | None, default_image: str | None) -> UserProfile:
    ...
```

Call sites:

1. `GET /public/profile/me` — first visit creates row
2. `create_comment` in `blog_social.py` — resolve `display_name` / `avatar_url` from profile before insert
3. Optional: admin seed script for existing users (one-off SQL or management command)

**Alternative (phase 2):** Better Auth `databaseHooks.user.create.after` in `frontend/lib/auth/server.ts` — only if lazy creation causes visible race in comments.

## Backend

### New module: `backend/app/user_profiles.py`

**`UserProfileRepository` protocol + InMemory + Postgres implementations.**

| Method | Purpose |
| --- | --- |
| `get_by_user_id(user_id)` | Nullable get |
| `get_or_create(user_id, defaults...)` | Lazy provision |
| `update(user_id, patch)` | Owner update |
| `list_for_admin(limit, offset)` | Admin directory |
| `get_public(user_id)` | Public card |

Postgres implementation may `JOIN "user"` for admin email.

### Routes: `create_user_profile_routes(repo, settings)`

| Method | Path | Auth | Behavior |
| --- | --- | --- | --- |
| GET | `/public/profile/me` | user | `get_or_create` from identity |
| PATCH | `/public/profile/me` | user | Update own profile |
| GET | `/public/profiles/{user_id}` | none | `UserProfilePublic` — 404 if no profile (or auto-create only for `/me`; public GET returns 404 until user has visited `/me` once — **prefer lazy create on any authenticated action** so commenters always have a row) |

**Admin:** `create_user_profile_admin_routes(repo, settings)`

| Method | Path | Auth | Behavior |
| --- | --- | --- | --- |
| GET | `/admin/user-profiles` | admin | Paginated list with email |

Wire in `main.py` via `app.include_router(...)`.

### Comment integration (`backend/app/blog_social.py`)

1. Inject `UserProfileRepository` into `create_blog_social_routes` (add parameter; update `create_app` wiring).
2. On `create_comment`:
   - `profile = profile_repo.get_or_create(user_id, default_name=..., default_image=None)`
   - Store `user_name=profile.display_name` on `BlogComment`
3. Extend `BlogCommentPublic`:

   ```python
   class BlogCommentPublic(BaseModel):
       id: str
       user_id: str  # new — enables profile link
       user_name: str | None = None
       avatar_url: str | None = None  # new
       ...
   ```

4. Map `avatar_url` from profile when listing approved comments.

**Note:** Existing comments keep old `user_name`; optional backfill not required.

### Frontend user boundary

Add `frontend/lib/user/fastapi-boundary.ts` (mirror `lib/admin/fastapi-boundary.ts`):

- Sign session → `x-ai-lab-user-identity` + signature headers
- Use for profile PATCH/GET and existing social calls if not already centralized

## Frontend

### Lib: `frontend/lib/user/profile.ts`

- `getMyProfile(session)`, `updateMyProfile(session, data)`, `getPublicProfile(userId)`

### Pages

| Route | File | Behavior |
| --- | --- | --- |
| `/profile` | `app/profile/page.tsx` | Server: session required → redirect login; show own `UserProfilePublic` + link to edit |
| `/profile/edit` | `app/profile/edit/page.tsx` | Form: display name, bio, avatar URL, website, GitHub, LinkedIn; server action PATCH |
| `/profiles/[userId]` | `app/profiles/[userId]/page.tsx` | Optional public profile page (linked from comments) |

Use `PublicPageShell` for public profile view; simple card layout consistent with `public-editorial-shell`.

### Navigation

- Add “Profile” link in public header when `session` (near blog / bookmarks)
- `app/bookmarks/page.tsx` area already assumes auth — same nav pattern

### Comment UI (`components/blog/blog-comments.tsx`)

- `CommentCard`: if `comment.avatar_url`, show `<Image>` or `<img>`; else keep letter avatar
- `user_name` links to `/profiles/{comment.user_id}` when `user_id` present
- On create comment, backend sets name from profile — no client change needed for content

### Auth signup

No frontend change required if lazy `get_or_create` on first `/public/profile/me` or first comment.

Optional: after signup redirect to `/profile/edit?welcome=1` (product polish, not blocking).

## Tests

### Backend (`backend/tests/test_user_profiles.py`)

- `get_or_create` idempotent
- Owner can PATCH; cannot PATCH another user (no route)
- Public GET omits email
- Admin list returns emails
- Comment create uses profile `display_name`

### E2E (optional)

- Register/login fixture → visit `/profile/edit` → update name → comment on post shows new name

## Verification commands

```bash
python -m alembic -c backend/alembic.ini upgrade head
uv run pytest backend/tests/test_user_profiles.py backend/tests/test_blog_social.py -q
cd frontend && npm run lint && npm run typecheck
```

## Harness / story follow-up

1. Story: `docs/stories/epics/E01-auth/US-0XX-user-profiles.md` (or E02 if grouped with blog social)
2. Update product docs if profiles are listed in overview
3. Trace + story proof update

## File checklist

| Action | Path |
| --- | --- |
| Add | `backend/app/user_profiles.py` |
| Edit | `backend/app/database.py` |
| Edit | `backend/app/blog_social.py` |
| Edit | `backend/app/main.py` |
| Add | `backend/migrations/versions/20260604_0027_user_profiles.py` |
| Add | `backend/tests/test_user_profiles.py` |
| Add | `frontend/lib/user/fastapi-boundary.ts` |
| Add | `frontend/lib/user/profile.ts` |
| Add | `frontend/app/profile/page.tsx` |
| Add | `frontend/app/profile/edit/page.tsx` |
| Add | `frontend/app/profiles/[userId]/page.tsx` |
| Edit | `frontend/components/blog/blog-comments.tsx` |
| Edit | `frontend/lib/blog/social.ts` (types) |
| Edit | public nav component(s) for Profile link |

## Security / privacy

- Never expose `email` on `/public/profiles/{id}`
- Validate URLs (http/https only) — reuse max length patterns from `image_url` on blog posts
- Profile PATCH requires signed user identity (same as comments)

## Out of scope

- Avatar upload to object storage (URL-only MVP)
- Profile visibility toggles (private account)
- Admin edit of user profiles
- Syncing `display_name` back to Better Auth `user.name` (one-way copy on create only)

## Dependency order

1. **User profiles** can ship before or after tags; no hard dependency.
2. If both in one sprint: tags first (no FK to profiles), then profiles + comment avatar pass.

## Risk notes

- **Medium:** FK to Better Auth `"user"` — migration must run after `20260602_0004`
- Comment Pydantic change is backward-compatible if `user_id` / `avatar_url` optional on client
