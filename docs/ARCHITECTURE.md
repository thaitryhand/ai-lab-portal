# Architecture

AI Lab Portal is a full-stack web application. This document records the
selected stack, layering, and boundary rules that govern implementation.

## Selected Stack

| Layer | Technology | Role |
| --- | --- | --- |
| Public + admin UI | Next.js 16 (App Router), React, TypeScript, Tailwind, shadcn/ui | Server components, server actions, public and admin surfaces |
| Auth | Better Auth | Session-based admin and public user identity |
| API | FastAPI (Python) | REST API, OpenAPI docs, admin/public route separation |
| Database | PostgreSQL + Alembic | Primary data store and migrations |
| Cache / broker | Redis | Celery broker and session-adjacent infra |
| Workers | Celery | Async jobs: AI generation, news crawl/extract/score, social ingest |
| LLM / extraction | OpenAI-compatible LLM service, Firecrawl (optional), fake providers for tests | Structured output, article extraction, scoring |
| Local orchestration | Docker Compose | Postgres, Redis, backend, frontend, worker services |
| E2E proof | Playwright | Browser workflows against Docker platform |
| Harness | Rust CLI (`scripts/bin/harness-cli`) + SQLite (`harness.db`) | Story matrix, traces, operational records |

Record significant stack changes in `docs/decisions/`.

## Repository Layout

```text
frontend/          Next.js app (public + admin routes, components, E2E tests)
backend/           FastAPI app (domain, repositories, routers, Celery tasks)
scripts/           Harness CLI, proof audits, seed scripts
docs/              Product spec, stories, architecture, decisions
docker-compose.yml Local dev stack
```

## Layering

```text
domain / repositories / services
  <- FastAPI routers (interface)
      <- Celery tasks (async application)
          <- Next.js server actions + route handlers (app surfaces)
```

Inner Python modules (`backend/app/`) follow a pragmatic layered style:
repositories encapsulate SQL, routers validate and authorize at boundaries,
Celery tasks orchestrate long-running pipelines.

## Public vs Admin Boundary

| Surface | Auth | Data access |
| --- | --- | --- |
| Public routes (`/blog`, `/ai-news`, `/projects`, …) | Optional session for social features | Published/read-only models via public API |
| Admin routes (`/admin/*`) | Better Auth session + admin role | Full CRUD, review queues, audit events |
| FastAPI admin routers | Signed identity header from Next.js proxy | `require_configured_admin_identity` |

Unknown data must be parsed at HTTP boundaries before entering repositories.

Boundaries include:

- HTTP request bodies, params, and query strings.
- Session payloads and identity claims.
- Environment variables (`AI_LAB_*` prefix).
- Database rows returned from repositories.
- Provider webhooks, Celery payloads, and extraction responses.

Target flow:

```text
unknown input
  -> Pydantic model / validator
  -> repository or service
  -> typed domain record
```

## Core Domains

| Domain | Key concepts |
| --- | --- |
| Blog CMS | Posts, drafts, publish/unpublish, audit, public read model |
| AI Blog Agent | Ideas, outlines, drafts, reviews, claims, `ai_runs`, generation jobs |
| AI News | Sources, raw items, extraction, dedup, scoring, review queue, publish |
| User-submitted links | Public submit form, SSRF validation, async pipeline merge |
| Social (X/Twitter) | Fake-first ingest contract, social scoring dimensions, admin review context |
| Blog social | Comments, reactions, bookmarks, follows, feeds, tags |
| Contact | Public form submissions, admin message list |
| Notifications | Follow/comment-reply events, unread counts |
| Projects | Slugged company projects (parallel to showcases) |
| Identity | Better Auth users, admin roles, public profiles |

## Async Pipelines

Celery workers handle:

- AI blog generation stages (outline, draft, review, marketing metadata).
- News RSS crawl, article extraction, dedup, scoring.
- User-submitted link processing.
- Social X/Twitter ingest (fake provider in current deployment).

Jobs are tracked in the database; admin UIs poll job status where needed.

## Observability Contract

The FastAPI server emits structured JSON log lines per request with:

- timestamp
- level
- request_id
- user_id when known
- action
- duration_ms
- status_code
- message

Audit logs are product records (`audit_events` table). Application logs are
operational records. Do not use one as a substitute for the other.

## Validation Ladder

Proof expectations per story layer (see `docs/HARNESS.md`):

1. **Unit** — pytest for backend logic, repository behavior.
2. **Integration** — API contract tests, migration smoke.
3. **E2E** — Playwright against Docker platform for user-visible flows.
4. **Platform** — Docker compose up, port/env alignment, deploy smoke.

Use `scripts/bin/harness-cli query matrix` and `scripts/proof_matrix_gaps.py`
to audit proof coverage.

## Dependency Rule

Inner layers must not depend on outer layers.

| Layer | May depend on | Must not depend on |
| --- | --- | --- |
| repositories / domain services | nothing project-external except pure utilities | FastAPI request objects, UI, provider SDKs directly in domain |
| FastAPI routers | repositories, services, Pydantic models | Next.js, Celery internals |
| Celery tasks | repositories, services | HTTP session state |
| Next.js surfaces | API contracts, auth session | Python domain internals directly |

## Command/Query Boundary

- Commands mutate state and own audit side effects (publish, approve, process job).
- Queries read state and format for consumers (public lists, admin dashboards).
- Shared domain rules live in repositories/services, not in route handlers.
