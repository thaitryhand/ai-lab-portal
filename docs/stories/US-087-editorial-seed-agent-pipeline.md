# US-087 Editorial Seed via Agent Pipeline

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — reproducible demo content through the real pipeline (2026-06-06).

## Product Contract

Operators can seed a published blog post by running the semi-auto agent pipeline
with deterministic fake LLM responses (no OpenAI key), using the same API path as
production admin workflows.

## Acceptance Criteria

1. `scripts/seed_blog_agent_pipeline.py` seeds a published project and runs generate → publish.
2. Script uses shared pipeline helpers in `scripts/blog_agent_common.py`.
3. Requires backend with `AI_LAB_LLM_E2E_FAKE=true` (documented).
4. Supports `--skip-publish`, `--no-waive-claims`, and `--idea-id` resume.
5. Outputs admin and public URLs on success.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A |
| Integration | Script against local backend + Postgres |
| E2E | Covered by US-086 Playwright golden path |
| Platform | `scripts/e2e-preflight.sh` before manual run |
| Release | Manual smoke: `python scripts/seed_blog_agent_pipeline.py` |

## Evidence

- `scripts/seed_blog_agent_pipeline.py`
- `scripts/blog_agent_common.py`
- `docs/local-dev.md` seed section
