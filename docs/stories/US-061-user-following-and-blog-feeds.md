# US-061 User Following and Blog Feeds

## Status

planned

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

Pending implementation.
