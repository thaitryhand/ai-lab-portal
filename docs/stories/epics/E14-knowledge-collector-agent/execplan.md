# Exec Plan

## Goal

Turn the existing KnowledgeService from a silent background helper into a
visible, testable, user-controllable pipeline stage with persistent storage
and admin review UI.

## Scope

In scope:

- `knowledge_contexts` DB table + Alembic migration.
- `KnowledgeContextRepository` (InMemory + Postgres).
- REST API: POST /admin/knowledge/collect (trigger collection for an idea).
- REST API: GET /admin/knowledge/context/{idea_id} (view collected context).
- REST API: PATCH /admin/knowledge/context/{idea_id} (edit collected context).
- Pipeline stepper: add "Collect Context" step between idea creation and outline.
- Admin UI for context review: show sources, let user edit, approve button.
- Integration into streaming routes: use stored context instead of live query.
- Tests: KnowledgeService unit tests, API integration tests, E2E new step.
- Backlog updates: close intake, update matrix, record trace.

Out of scope:

- Multi-source agentic orchestration (phase 2).
- Auto-collect on idea creation.
- Context version history.

## Risk Classification

Risk flags:

- **Data model** — new `knowledge_contexts` table + migration.
- **Existing behavior** — modifies pipeline stepper, streaming routes.
- **Weak proof** — KnowledgeService has zero tests.
- **Multi-domain** — touches projects, blog, showcases, news queries.

No hard gates (no auth, authorization, data loss, audit/security, external provider).

## Work Phases

1. **Discovery** — review existing KnowledgeService, pipeline stepper, streaming routes.
2. **Design** — data model, API contracts, UI sketch.
3. **Validation planning** — test plan for each layer.
4. **Implementation** — migration, repository, API, pipeline step, UI, tests.
5. **Verification** — run tests, verify pipeline step in E2E.
6. **Harness update** — record intake, add story, matrix, trace.

## Stop Conditions

Pause for human confirmation if:

- Product behavior is ambiguous about what context should be visible.
- Data migration or deletion risk appears (existing ideas with no context).
- Validation requirements need to be weakened.
- Architecture direction changes (e.g., switching to agent-only collection).
