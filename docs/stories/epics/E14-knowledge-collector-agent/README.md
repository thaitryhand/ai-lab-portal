# E14 Knowledge Collector Agent

Make knowledge collection a visible, agent-driven pipeline stage in the blog ideas workflow.

## Motivation

Knowledge collection existed as a hidden backend service wired into the streaming routes. It had no visible UI, no persistence, no tests, and no way for admin operators to review or edit collected context before AI generation. This epic makes it a first-class pipeline step.

## Stories

| Story | Scope | Status |
|---|---|---|
| **INIT-KC-001** | Pipeline step, admin review UI, persistent storage, tests, agent integration | **Implemented** |

## What Was Built

### Pipeline Step
- New "Context" step (step 2) between "Idea" (step 1) and "Outline" (step 3)
- All pipeline files updated: `pipeline-step-nav.tsx`, `pipeline-step-shell.tsx`, `pipeline-next-action.ts`, `pipeline-next-stage.ts`
- Step state machine: `null` → "collect" button → "collected" → "approve" button → "approved" → pipeline proceeds

### Admin Review UI
- "Collect context" button triggers `POST /admin/knowledge/collect`
- Status display in the step body: "No context collected yet" / "Context collected — review and approve" / "Context approved"
- "Approve context" button advances the pipeline

### Backend API
| Method | Endpoint | Action |
|---|---|---|
| POST | `/admin/knowledge/collect` | Trigger collection |
| GET | `/admin/knowledge/context/{idea_id}` | View collected context |
| PATCH | `/admin/knowledge/context/{idea_id}` | Edit context |
| PATCH | `/admin/knowledge/context/{idea_id}/approve` | Approve & advance |

### Persistent Storage
- `knowledge_contexts` table in Postgres
- `KnowledgeContextRepository` ABC with InMemory + Postgres implementations
- Unique constraint per `blog_idea_id`

### Tests
- 13 unit tests for `KnowledgeService` and `KnowledgeContextRepository`
- All tests pass in-memory mode

## Key Files

| File | Purpose |
|---|---|
| `backend/migrations/versions/20260608_0042_knowledge_contexts.py` | Database migration |
| `backend/app/knowledge_context.py` | Models, repositories, API routes |
| `backend/app/knowledge_collector.py` | `KnowledgeService` with in-memory fake |
| `backend/app/database.py` | Table definition |
| `backend/app/main.py` | Route wiring |
| `backend/app/blog_ideas.py` | `knowledge_context_status` field + API merge |
| `backend/tests/test_knowledge_collector.py` | 13 unit tests |
| `frontend/app/admin/blog-ideas/idea-detail-view.tsx` | Collect step shell UI |
| `frontend/app/admin/blog-ideas/pipeline-step-nav.tsx` | Context step in stepper |
| `frontend/app/admin/blog-ideas/pipeline-step-shell.tsx` | Collect step order |
| `frontend/app/admin/blog-ideas/lib/pipeline-next-action.ts` | Collect state machine |
| `frontend/app/admin/blog-ideas/lib/pipeline-next-stage.ts` | Collect approve gate |
| `frontend/app/admin/blog-ideas/lib/pipeline-next-action.test.ts` | Updated test fixtures |

## Exit Criteria

- [x] Pipeline stepper shows "Context" step between Idea and Outline
- [x] Admin can trigger knowledge collection and see status
- [x] Admin can review and approve collected context
- [x] Pipeline advances to Outline after approval
- [x] `knowledge_context_status` visible in BlogIdea API response
- [x] 13+ unit tests pass
- [x] Frontend typecheck passes
