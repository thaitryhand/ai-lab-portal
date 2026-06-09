# US-108 Auto-Scheduling Agent

## Status

planned

## Lane

normal

## Intake

#116 — AI Agents Expansion

## Product Contract

Build an AI agent that analyzes content readiness, calendar context, and historical engagement patterns to suggest optimal publishing times for approved blog posts. Integrates with the existing pipeline publish step.

## Epic

E16-ai-agents-expansion

## Affected Docs

- `backend/app/scheduling_agent.py` — new module (agent logic + calendar awareness)
- `backend/app/llm/prompts.py` — add scheduling prompt templates
- `backend/app/llm/e2e_fake_responses.py` — add fake scheduling responses
- `backend/app/blog_ideas.py` — extend `scheduled_at` logic
- `frontend/app/admin/blog-ideas/idea-detail-view.tsx` — add scheduling UI
- `frontend/app/admin/content-calendar/` — extend existing calendar

## Acceptance Criteria

1. After a blog post is approved for publish, agent analyzes:
   - Content readiness (all pipeline stages complete ✅)
   - Calendar context (weekday vs weekend, holidays, existing scheduled posts)
   - Historical engagement patterns (which days/times perform best, from US-103/104 data)
2. Agent returns: `{ suggested_date, suggested_time, rationale, confidence }`
3. Admin sees scheduling suggestion in the publish step UI
4. Admin can: accept suggestion, pick different date, or publish immediately
5. Scheduled posts auto-publish at the designated time (via Celery periodic task)
6. Content calendar view (`/admin/content-calendar`) shows scheduled posts
7. Fake provider returns plausible scheduling suggestions for testing
8. Frontend typecheck, lint, and build pass

## Non-Goals

- No automatic publishing without admin confirmation
- No timezone detection per reader (uses portal's configured timezone)
- No A/B testing of publish times

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Scheduling agent produces valid date/time suggestions |
| Integration | API returns scheduling recommendations |
| E2E | Playwright: scheduling suggestion appears in publish flow |
| Platform | Celery periodic task for auto-publish |
| Release | `cd frontend && npm run typecheck && npm run lint && npm run build` |
