# US-091 Agents SDK Backend Option

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — OpenAI Agents SDK integration for pipeline generation (2026-06-06).

## Product Contract

The blog agent pipeline can use either the existing OpenAI structured-output service or the OpenAI Agents SDK as the LLM backend, selectable via `AI_LAB_LLM_BACKEND` env var (`openai` or `agents_sdk`). Agents SDK backend constructs with key/model, raises `KeyError` on unknown prompts, and handles missing API key gracefully.

## Acceptance Criteria

1. `AI_LAB_LLM_BACKEND=agents_sdk` selects the Agents SDK backend.
2. `AI_LAB_LLM_BACKEND=openai` selects the original service (default).
3. `AgentsSDKLLMService` constructs with key/model and validates prompt registry.
4. Unknown prompt names raise `KeyError`.
5. Missing API key handled gracefully.
6. E2E fake mode (`AI_LAB_LLM_E2E_FAKE=true`) takes precedence over backend selection.
7. Full backend test suite passes.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | 28/28 LLM tests pass (21 original + 7 new) |
| Integration | N/A |
| E2E | N/A |
| Platform | N/A |
| Release | Full backend suite 916/916 pass (alembic head mismatch resolved) |

## Evidence

- `backend/app/llm/service.py` — backend selection via env var
- `backend/app/llm/agents_sdk_service.py` — Agents SDK integration
