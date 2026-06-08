# US-100 AI Lab Tour — Pipeline Stage Showcase

## Status

implemented

## Lane

normal

## Intake

#112 AI Lab Tour page — interactive 7-stage pipeline showcase (2026-06-08).

## Product Contract

The AI Lab Tour page at `/tour` includes an interactive Pipeline section that visualises the 7-stage AI content pipeline: Idea, Outline, Draft, Marketing, Claims, SEO, Publish. Each stage is rendered as a terminal-style card with stage name, fake LLM response (terminal output), status badge, and duration. Uses framer-motion staggered animations on scroll. Powered by deterministic fake LLM data from `e2e_fake_responses.py`.

## Acceptance Criteria

1. 7 pipeline stage cards rendered in order: Idea → Outline → Draft → Marketing → Claims → SEO → Publish.
2. Each card shows: stage name, terminal output text, status badge, processing time.
3. Cards animate in with staggered entrance on scroll.
4. Data sourced from deterministic fake LLM responses.
5. Responsive layout (single column on mobile, 2-column grid on desktop).

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A |
| Integration | N/A |
| E2E | Manual: All 7 cards render with content, animations work on scroll |
| Platform | Frontend typecheck passes |
| Release | No backend dependencies |

## Evidence

- `frontend/components/tour/tour-pipeline.tsx` — Pipeline component with 7 stage cards
- `backend/app/llm/e2e_fake_responses.py` — Deterministic fake LLM responses
