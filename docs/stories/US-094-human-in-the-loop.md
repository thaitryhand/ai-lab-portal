# US-094 Human-in-the-Loop via Agent Sessions

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — human approval gates as agent session interrupts (2026-06-06).

## Product Contract

Pipeline agents can pause execution at approval gates and resume when the human operator approves or rejects, using the Agents SDK's human-in-the-loop primitives. Each gate produces a structured approval request visible in the admin UI.

## Acceptance Criteria

1. Pipeline pauses at each gate until human decision.
2. Approval gates: idea, outline, draft, review, marketing, SEO audit.
3. Admin UI displays pending approval requests.
4. Agent session resumes with human decision context.
5. Unit tests pass for session lifecycle.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Session lifecycle tests pass |
| Integration | N/A |
| E2E | N/A |
| Platform | N/A |
| Release | Full backend suite passes |

## Evidence

- `backend/app/agents/human_in_loop.py` — approval gate primitives
- `backend/app/agents/session_manager.py` — agent session lifecycle
