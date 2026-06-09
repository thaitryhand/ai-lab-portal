# Validation

## Proof Strategy

Before the story is done:

1. Unit tests pass for KnowledgeService with real + InMemory implementations.
2. Integration tests pass for all 3 knowledge API endpoints.
3. Pipeline stepper shows the new "Collect Context" step.
4. Admin can collect, view, edit, and approve context via the UI.
5. Frontend typecheck, lint, and build pass.
6. Backend full test suite passes.
7. E2E test verifies the collect → approve → generate flow.

## Test Plan

| Layer | Cases |
|-------|-------|
| Unit | `KnowledgeService.collect_for_project()` queries all 4 sources; handles empty results; InMemoryKnowledgeService returns expected structure |
| Unit | `KnowledgeContextRepository` create, get by idea, update, approve |
| Integration | POST /admin/knowledge/collect returns context for valid idea |
| Integration | GET /admin/knowledge/context/{idea_id} returns stored context |
| Integration | PATCH /admin/knowledge/context/{idea_id} updates editable fields |
| Integration | PATCH /admin/knowledge/context/{idea_id}/approve sets approved_at |
| E2E | admin-proof-gaps: collect context, view review UI, approve, verify pipeline advances |
| Platform | N/A (no new infra) |

## Fixtures

- Seeded project, blog post, showcase, and news items in the database.
- Admin user with session for E2E.

## Commands

```text
python -m pytest backend/tests/test_knowledge_collector.py -q
cd frontend && npm run typecheck
cd frontend && npm run lint
cd frontend && npm run test:e2e -- admin-proof-gaps
```

## Acceptance Evidence

TBD — add results after verification.
