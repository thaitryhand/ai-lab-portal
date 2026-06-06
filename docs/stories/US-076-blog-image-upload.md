# US-076 Blog Image Upload and Persistence

## Status

implemented

## Lane

normal

## Intake

Retroactive — harness hygiene sync (2026-06-06).

## Product Contract

Blog authors need inline image upload in the TipTap editor with URLs that
survive Docker rebuilds and publish flows without losing editor content.

## Acceptance Criteria

1. Admin/public blog editor supports image upload and renders images in posts.
2. Uploaded images persist across Docker container rebuilds (volume mount).
3. Save draft and publish flows preserve editor image URLs (no stale hidden input).
4. Publish action does not bypass saveDraft and lose content on existing posts.
5. Backend tests and frontend quality gate pass.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A |
| Integration | Upload endpoint and blog save regression tests |
| E2E | Blog editor image smoke where covered |
| Platform | Docker volume persistence verified manually |
| Release | Backend pytest + frontend typecheck/lint/build |

## Evidence

- Commit `2b3e813` — feat: add image upload and rendering for blog posts
- Commit `68adf12` — fix: persist uploaded images across Docker rebuilds
- Commit `19c3beb` — fix: remove throttle delay preventing image URLs from saving
- Commit `66be0c1` — fix: sync hidden input DOM value at submit time
- Commit `4c73ab9` — fix: publishAction bypassed saveDraft for existing posts
