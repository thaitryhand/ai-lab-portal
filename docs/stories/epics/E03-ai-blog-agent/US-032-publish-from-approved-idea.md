# US-032 Publish From Approved Idea

## Status

implemented

## Lane

normal

## Product Contract

When a blog idea has passed draft, technical review, and marketing approval, an admin can bridge it into the manual CMS by creating and publishing a `blog_post` in one action. The idea stores `published_blog_post_id` for idempotent follow-up visits.

## Relevant Product Docs

- `docs/product/blog-agent.md`
- `docs/product/mvp-roadmap.md` (MVP 2 publish bridge)

## Acceptance Criteria

- `POST /admin/blog-ideas/{id}/publish-to-blog` validates approved draft, technical review, and marketing metadata.
- Endpoint creates a blog post (title/excerpt/slug from marketing metadata, body from draft markdown) and publishes it.
- Idea records `published_blog_post_id`; repeat calls return the existing post without duplicating.
- Admin idea detail shows **Publish to blog** when ready and CMS/public links when linked.
- Audit events: `blog_post.created`, `blog_post.published`, `blog_idea.published_to_blog`.

## Design Notes

- Bridge logic: `backend/app/blog_publish.py`
- Route: `create_blog_idea_routes` → `publish-to-blog`
- Migration: `20260603_0011_blog_ideas_published_post.py`
- UI: `frontend/app/admin/blog-ideas/idea-detail-view.tsx`, `actions.ts`

## Validation

`scripts/bin/harness-cli story update --id US-032 --unit 1 --integration 1 --e2e 0 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | `backend/tests/test_blog_publish.py` |
| Integration | API publish route + blog public list |
| E2E | Not required for this slice |
| Platform | Not required |

## Evidence

- 2026-06-03: `python -m pytest backend/tests/test_blog_publish.py` → 7 passed.
- E2E is marked `n/a` per this story's validation contract: publish bridge proof is backend/API integration, not a browser slice.
