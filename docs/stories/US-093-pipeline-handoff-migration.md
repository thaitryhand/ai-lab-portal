# US-093 Pipeline Handoff Migration

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — migrate pipeline stages from direct OpenAI calls to handoff-based agent pipeline (2026-06-06).

## Product Contract

Pipeline stages (outline, draft, review, marketing, claims, SEO audit) are refactored to use a handoff-based agent architecture instead of direct LLM service calls, enabling the Agents SDK to orchestrate multi-stage pipelines.

## Acceptance Criteria

1. Each pipeline stage is represented as an agent with handoff capabilities.
2. Handoff chain: idea → outline → draft → review → marketing → SEO → claims.
3. Existing API endpoints remain backward compatible.
4. Unit tests pass for handoff wiring.
5. Full backend suite passes.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Handoff wiring tests pass |
| Integration | Pipeline integration tests pass |
| E2E | N/A |
| Platform | N/A |
| Release | Full backend suite passes |

## Evidence

- `backend/app/agents/pipeline_handoff.py` — handoff agent chain
- `backend/app/agents/handoff_stages.py` — per-stage agent definitions
