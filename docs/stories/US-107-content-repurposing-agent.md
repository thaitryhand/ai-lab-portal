# US-107 Content Repurposing Agent

## Status

planned

## Lane

normal

## Intake

#116 — AI Agents Expansion

## Product Contract

Build an AI agent that transforms a published blog post into social media content: Twitter thread, LinkedIn article, and short summary snippets. Uses the existing LLM service and prompt registry.

## Epic

E16-ai-agents-expansion

## Affected Docs

- `backend/app/content_repurpose.py` — new module (agent logic + prompts + API)
- `backend/app/main.py` — wire routes
- `backend/app/llm/prompts.py` — add repurposing prompt templates
- `backend/app/llm/e2e_fake_responses.py` — add fake responses for repurposing
- `frontend/app/admin/blog-posts/[id]/repurpose/page.tsx` — new admin UI
- `frontend/app/blog/[slug]/page.tsx` — add "Share" dropdown

## Acceptance Criteria

1. `POST /admin/blog-posts/{id}/repurpose` triggers agent to generate:
   - Twitter thread (5-10 tweets with thread numbering)
   - LinkedIn article (headline + summary + key takeaways)
   - Short summary snippet (2-3 sentences for social sharing)
2. Agent uses the existing LLM service (respects `AI_LAB_LLM_BACKEND` setting)
3. Generated content is stored in a `repurposed_content` table (JSONB per platform)
4. Admin can view/edit generated content before using
5. "Copy to clipboard" buttons for each format
6. "Share" dropdown on public blog post page shows:
   - "Share on Twitter" — opens Twitter intent with generated thread
   - "Share on LinkedIn" — opens LinkedIn with generated article
   - "Copy link" — copies blog URL
7. Fake provider returns realistic mock content for testing
8. Frontend typecheck, lint, and build pass

## Non-Goals

- No auto-posting to social media (manual copy-paste only)
- No scheduling — that's US-108
- No image/media generation

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Repurposing agent produces correct output format for each platform |
| Integration | API endpoint returns generated content |
| E2E | Playwright: admin repurpose flow, share buttons visible |
| Platform | N/A |
| Release | `cd frontend && npm run typecheck && npm run lint && npm run build` |
