# US-092 Agents SDK E2E with Fake Provider

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — verify Agents SDK backend works end-to-end with fake provider (2026-06-06).

## Product Contract

The Agents SDK backend produces identical fake output as the OpenAI service backend when `AI_LAB_LLM_E2E_FAKE=true`. Factory returns correct service type for both backends. `RecordingLLMService` wraps `AgentsSDKLLMService` for trace recording.

## Acceptance Criteria

1. Factory returns correct service type for `openai` and `agents_sdk` backends.
2. `RecordingLLMService` wraps `AgentsSDKLLMService`.
3. Fake output identical regardless of backend setting.
4. E2E fake mode (`AI_LAB_LLM_E2E_FAKE=true`) overrides `agents_sdk` backend.
5. Provider names match backend setting.
6. 10/10 integration tests pass.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Factory returns correct type for both backends |
| Integration | 10/10 tests in `test_blog_agents_sdk.py` |
| E2E | N/A |
| Platform | N/A |
| Release | Full backend suite 916/916 pass (alembic head mismatch resolved) |

## Evidence

- `backend/tests/test_blog_agents_sdk.py` — 10 integration tests
- `backend/app/llm/factory.py` — backend-aware service factory
