# US-109 SEO Auto-Optimize Agent

## Status

planned

## Lane

normal

## Intake

#116 — AI Agents Expansion

## Product Contract

Build an AI agent that analyzes SEO audit results (from the existing pipeline step 7) and automatically applies recommendations to the blog post content — improving headings, meta descriptions, internal links, and keyword placement.

## Epic

E16-ai-agents-expansion

## Affected Docs

- `backend/app/seo_optimizer.py` — new module (agent logic)
- `backend/app/llm/prompts.py` — add SEO optimization prompts
- `backend/app/llm/e2e_fake_responses.py` — add fake SEO responses
- `backend/app/blog_ideas.py` — extend draft/content update
- `frontend/app/admin/blog-ideas/idea-detail-view.tsx` — add "Auto-optimize SEO" button

## Acceptance Criteria

1. After SEO audit completes (pipeline step 7), admin sees "Auto-optimize SEO" action
2. Agent analyzes the SEO audit output and applies:
   - Title improvements (without losing original meaning)
   - Meta description rewrite
   - Heading structure improvements (H1/H2/H3 hierarchy)
   - Internal link suggestions (linking to other relevant posts)
   - Keyword placement optimization
3. Agent returns a diff showing what changed (before/after per section)
4. Admin can review changes and accept/reject per section
5. Accepted changes are applied to the draft content
6. Agent uses existing LLM service (respects `AI_LAB_LLM_BACKEND`)
7. Fake provider returns sample diffs for testing
8. No changes are applied without explicit admin approval
9. Frontend typecheck, lint, and build pass

## Non-Goals

- No automatic application without admin review
- No external SEO tool integration (uses internal audit results only)
- No image alt-text generation (deferred)
- No schema.org markup generation

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | SEO optimizer produces valid before/after diffs |
| Integration | API returns optimization suggestions |
| E2E | Playwright: "Auto-optimize SEO" button visible after audit |
| Platform | N/A |
| Release | `cd frontend && npm run typecheck && npm run lint && npm run build` |
