# US-096 Agents SDK Tracing into ai_runs

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — trace Agents SDK execution into the ai_runs table for observability (2026-06-06).

## Product Contract

Each Agents SDK run produces a trace record in the `ai_runs` table, capturing prompt name, status, tokens, latency, provider, model, and trace_id. This enables the observability dashboard (US-097) to show per-pipeline-stage metrics.

## Acceptance Criteria

1. `RecordingLLMService` wraps Agents SDK runner and records runs.
2. Each run captures: prompt_name, status, tokens (prompt/completion/total), latency_ms, provider, model.
3. Trace ID from Agents SDK linked to `ai_runs` record.
4. Failed runs include error_message.
5. Unit tests pass for tracing integration.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Tracing integration tests pass |
| Integration | N/A |
| E2E | N/A |
| Platform | N/A |
| Release | Full backend suite passes |

## Evidence

- `backend/app/agents/recording_service.py` — tracing wrapper
- `backend/app/models/ai_run.py` — ai_runs model schema
