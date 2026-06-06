# US-078 Blog Social Hardening

## Status

implemented

## Lane

normal

## Intake

Retroactive — harness hygiene sync (2026-06-06).

## Product Contract

Blog social features need production-quality comment threads, reactions,
bookmarks, and editor UX so public readers and authors can engage reliably.

## Acceptance Criteria

1. Comment threads use TipTap WYSIWYG editor for compose and edit modes.
2. Comment reactions API and UI are wired (`blog_comment_reactions`).
3. Authenticated users can bookmark blog posts from list views.
4. Comments auto-approve for MVP social flow (documented behavior).
5. Public header redesign supports social navigation affordances.
6. E2E blog-social spec covers comment and reaction flows.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Backend comment/reaction tests |
| Integration | Comment and reaction API regression |
| E2E | `frontend/tests/e2e/blog-social.spec.ts` |
| Platform | N/A |
| Release | Backend pytest + frontend quality gate |

## Evidence

- Commit `0e56322` — feat: redesign blog comments with TipTap editor
- Commit `5a454f4` — feat: add blog_comment_reactions table and API endpoints
- Commit `1fd4943` — feat: redesign public header and add list bookmarks
- Commit `e3dc104` — fix: use TipTap WYSIWYG editor for edit mode
- Commit `bf15c0e` — feat: comment edit indicator
- Commit `6109a52` — feat(ui): improve comment thread line and header active nav styling
