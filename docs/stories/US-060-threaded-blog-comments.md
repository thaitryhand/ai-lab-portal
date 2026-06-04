# US-060 Threaded Blog Comments

## Status

implemented

## Lane

normal

## Product Contract

Blog comments support multi-level threaded discussion. Readers can reply to comments, see nested replies visually grouped under parents, and each comment shows the author profile identity where available.

## Relevant Product Docs

- `docs/product/blog-agent.md`
- `docs/plans/user-profiles-implementation.md`

## Current State

Implemented:

- `blog_comments.parent_id` exists.
- Backend accepts `parent_id` when creating a comment.
- Frontend comment form has a reply action.

Gap:

- Comment UI currently renders comments as a flat sorted list.
- No nested tree rendering.
- No maximum depth rule.
- Comment author display uses `user_name` only; no profile avatar or profile link.
- Public unauthenticated readers currently see sign-in prompt and no fetched approved comments because comment fetch is session-gated in `app/blog/[slug]/page.tsx`.

## Acceptance Criteria

- Approved comments are visible to all readers, including unauthenticated users.
- Authenticated users can reply to a comment.
- Replies render nested below their parent with indentation and visual grouping.
- Thread depth is capped (default: 3 visible levels; deeper replies flatten or show “replying to” affordance).
- Comment cards show:
  - display name;
  - avatar when profile has `avatar_url`;
  - link to `/profiles/{user_id}` when profile exists.
- Pending comments show a clear “awaiting moderation” state for the submitting user.
- Admin moderation still controls whether comments become publicly visible.

## Design Notes

- Commands:
  - `POST /public/blog-posts/{slug}/comments` keeps `parent_id`.
- Queries:
  - `GET /public/blog-posts/{slug}/comments` should not require signed user identity for approved comments.
  - Optionally add `GET /public/blog-posts/{slug}/comments/me` for pending comments by current user.
- API:
  - Extend `BlogCommentPublic` with `user_id`, `avatar_url`, maybe `status` for own pending items.
- Tables:
  - Existing `blog_comments.parent_id` sufficient.
  - Use `user_profiles` for avatar/name enrichment.
- Domain rules:
  - Parent must belong to same post.
  - Rejected comments never appear publicly.
  - Pending comments only visible to creator/admin.
- UI surfaces:
  - `frontend/components/blog/blog-comments.tsx`
  - `frontend/lib/blog/social.ts`
  - `frontend/app/blog/[slug]/page.tsx`

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Backend tests for public approved comments without auth, parent validation, pending visibility. |
| Integration | Comment tree building from flat API response. |
| E2E | Optional: user replies to a comment; approved nested reply appears under parent. |
| Platform | n/a unless deployed. |
| Release | Backend social/profile tests; frontend typecheck/lint/build. |

## Harness Delta

None expected.

## Evidence

Implemented in code:

- `GET /public/blog-posts/{slug}/comments` no longer requires signed user identity for approved comments.
- `BlogCommentPublic` now includes `user_id` and optional `avatar_url`.
- Comment creation uses `user_profiles` to persist profile display names.
- `components/blog/blog-comments.tsx` renders comment trees using `parent_id`, nested visual grouping, profile links, avatars, and moderation notice for new comments.

Validation run:

```text
python -m pytest backend/tests/test_blog_social_comments.py backend/tests/test_user_profiles.py -q
# 6 passed

cd frontend && npm run typecheck
# passed

cd frontend && npm run lint
# passed
```

