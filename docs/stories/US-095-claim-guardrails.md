# US-095 Claim Guardrails

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — guardrails that prevent publishing when claims are unsupported or unwaived (2026-06-06).

## Product Contract

Claim extraction and publish guardrails prevent publishing when claims have unresolved blocking status (pending or unsupported). Guardrails are enforced at both the UI and API levels, with clear messaging about what blocks publishing.

## Acceptance Criteria

1. Publish API rejects when blocking claims exist.
2. Admin UI disables publish button with explanation.
3. Waiving all claims clears the publish block.
4. Guardrails apply to both manual publish and agent pipeline publish.
5. Unit tests pass for guardrail logic.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Guardrail logic tests pass |
| Integration | N/A |
| E2E | N/A |
| Platform | N/A |
| Release | Full backend suite passes |

## Evidence

- `frontend/app/admin/blog-ideas/lib/claim-publish-gate.ts` — publish gate logic
- `backend/app/agents/claim_guardrails.py` — API-level guardrails
