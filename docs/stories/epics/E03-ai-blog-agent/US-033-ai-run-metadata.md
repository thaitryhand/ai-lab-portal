# US-033 AI Run Metadata Persistence

## Status

implemented

## Product Contract

Each important LLM call for a blog idea records provider, model, prompt name/version, inputs, outputs, token usage, and latency in `ai_runs`.

## Validation

`scripts/bin/harness-cli story verify US-033` → `python -m pytest backend/tests/test_blog_observability.py -k recording`

## Evidence

- `backend/app/ai_runs.py`, `backend/app/llm/recording.py`, migration `20260603_0012`
- `backend/tests/test_blog_observability.py` (`test_recording_service_persists_run`)
- E2E is marked `n/a`: this persistence contract has no browser-visible workflow by itself.
