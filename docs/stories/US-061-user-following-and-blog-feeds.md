# US-061 User Following and Blog Feeds

## Status

implemented

## Lane

normal

## Product Contract

Authenticated users can follow other users/authors. Blog discovery supports dev.to-like feeds:

- **Following** — posts by followed users/authors.
- **Latest** — newest published posts.
- **Discover** — broader public feed, optionally ranked by reactions/comments/bookmarks later.

## Relevant Product Docs

- `docs/product/blog-agent.md`
- `docs/plans/user-profiles-implementation.md`

## Current State

Implemented:

- Public user profiles exist (`/profile`, `/profile/edit`, `/profiles/{userId}`).
- Blog posts have `author_name` string but no `author_user_id`.
- Bookmarks/reactions/comments are user-scoped.

Gap:

- No `user_follows` table.
- No follow/unfollow API.
- No follow button on profile pages.
- No blog post ownership link to a user profile.
- No `/blog?feed=following|latest|discover` or tabs on blog index.
- `Latest` is effectively current default sort but not explicit.
- `Discover` ranking does not exist.

## Acceptance Criteria

- Users can follow/unfollow another user from `/profiles/{userId}`.
- Users cannot follow themselves.
- Follow count and following state display on profile pages.
- Blog index includes tabs/filters:
  - `Latest` — newest published posts.
  - `Following` — only posts by followed users/authors; requires login, otherwise prompts sign-in.
  - `Discover` — public feed, initially same as Latest or light ranking by engagement.
- Blog posts authored by authenticated users store `author_user_id` when created from public `/blog/new` or authenticated editor flows.
- Following feed filters by `author_user_id`.
- Existing anonymous/admin-authored posts continue to display by `author_name` and can appear in Latest/Discover.

## Design Notes

- Commands:
  - `POST /public/profiles/{user_id}/follow`
  - `DELETE /public/profiles/{user_id}/follow`
- Queries:
  - `GET /public/profiles/{user_id}/follow-state`
  - `GET /public/blog-posts?feed=latest|following|discover`
- API:
  - Extend signed user boundary routes in a new `user_follows.py` module.
- Tables:
  - `user_follows(follower_user_id, followed_user_id, created_at)` with composite PK.
  - Add nullable `author_user_id` to `blog_posts` or create mapping table if avoiding blog post schema change.
- Domain rules:
  - `follower_user_id != followed_user_id`.
  - Following feed requires auth.
  - Discover ranking can start as Latest but must be explicitly separated for future ranking.
- UI surfaces:
  - `/blog` feed tabs.
  - `/profiles/[userId]` follow button and counts.
  - `BlogEditor`/server actions assign `author_user_id` when session exists.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Backend tests for follow/unfollow, self-follow rejection, following feed filtering. |
| Integration | Blog post create assigns `author_user_id` for authenticated user. |
| E2E | Optional: user follows author, following feed shows author's post. |
| Platform | n/a unless deployed. |
| Release | Backend tests; frontend typecheck/lint/build. |

## Harness Delta

None expected.

## Evidence

Implemented in code:

- `backend/migrations/versions/20260604_0028_user_follows_blog_authors.py` adds `user_follows` and `blog_posts.author_user_id`.
- `backend/app/user_follows.py` adds follow/unfollow/follow-state repository and public routes.
- `GET /public/blog-posts?feed=latest|following|discover` supports explicit feed selection; Following requires signed user identity and filters by followed `author_user_id`.
- `BlogEditor` save/publish actions send `author_user_id` from the authenticated session.
- `/profiles/[userId]` displays follower/following counts and follow/unfollow affordances.
- `/blog` displays `Latest`, `Following`, and `Discover` tabs.

Validation run:

```text
python -m pytest backend/tests/test_user_follows.py backend/tests/test_user_profiles.py backend/tests/test_blog_social_comments.py backend/tests/test_blog_tags.py backend/tests/test_admin_blog.py backend/tests/test_migrations.py -q
# 22 passed

cd frontend && npm run typecheck
# passed

cd frontend && npm run lint
# passed

cd frontend && npm run build
# passed; routes include /blog and /profiles/[userId]
```

