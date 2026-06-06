# US-077 Public Profile Avatar and Cover Uploads

## Status

implemented

## Lane

normal

## Intake

Retroactive — harness hygiene sync (2026-06-06).

## Product Contract

Authenticated users can customize public profiles with avatar and cover image
uploads. The site header reflects the viewer's avatar without flicker on
navigation.

## Acceptance Criteria

1. Profile edit page supports avatar and cover image upload.
2. Public profile pages display uploaded avatar and cover.
3. Site header shows stable viewer avatar state across navigations.
4. Profile and edit-profile pages match redesigned visual standard.
5. Frontend typecheck, lint, and build pass.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A |
| Integration | Profile upload API tests if present |
| E2E | Profile smoke in Playwright where covered |
| Platform | N/A |
| Release | Frontend quality gate |

## Evidence

- Commit `cb34057` — feat(profile): add avatar and cover uploads
- Commit `91935b1` — fix(header): stabilize viewer avatar state
- Commit `d2b617e` — feat: redesign profile and edit profile pages
