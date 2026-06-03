# AI Lab Portal MVP Roadmap

## Implementation Principle

Build vertical slices. Do not build every module in the specification at once.
Each slice must have explicit data, API, security, provider behavior, and
validation contracts before implementation.

## Status Summary

| MVP | Objective | Status | Stories (representative) |
| --- | --- | --- | --- |
| MVP 0 | Foundation | **Implemented** | US-001 |
| MVP 1 | Manual CMS + public pages | **Implemented** | US-005–US-022 |
| MVP 2 | AI-assisted blog | **In progress** | US-025–US-035 |
| MVP 3 | AI News (official sources) | **Implemented** | US-036–US-041 |
| MVP 4 | User-submitted links | Planned | — |
| MVP 5 | X/Twitter intelligence | Blocked | — |

---

## MVP 0: Foundation

**Status: Implemented** (2026-06-02)

Objective: create the application foundation needed by later product slices.

Features:

- Next.js public/admin frontend shell.
- FastAPI backend with health endpoint and OpenAPI docs.
- PostgreSQL connection and Alembic migration setup.
- Redis connection.
- Celery worker and scheduler setup.
- Structured JSON logging.
- Environment configuration validation.
- Docker Compose for local development.

Success criteria:

- [x] Backend health endpoint returns success.
- [x] Frontend dev server renders a base shell.
- [x] Database migrations run from an empty database.
- [x] Worker executes a smoke-test job.
- [x] Secrets are loaded from environment variables and never committed.

---

## MVP 1: Manual AI Lab CMS and Public Pages

**Status: Implemented** (2026-06-02)

Objective: launch a credible AI Lab web presence before AI automation.

### Delivered

| Area | Routes / capability | Notes |
| --- | --- | --- |
| Public | `/`, `/lab`, `/showcases`, `/showcases/[slug]`, `/blog`, `/blog/[slug]` | Shared `PublicSiteShell`, shadcn theme tokens, SEO metadata (US-022) |
| Admin CMS | `/admin`, `/admin/blog/*`, `/admin/showcases/*` | Better Auth, shadcn admin shell, Tiptap editor, pending submit states |
| API | Blog + showcase CRUD, publish/unpublish, public read models | FastAPI + PostgreSQL + audit events |
| Proof | Backend tests, frontend typecheck/lint/build, Playwright E2E (7 tests) | React Doctor **100/100** with no issues found at MVP 1 close (US-023) |

### Deferred from original MVP 1 scope

| Item | Reason |
| --- | --- |
| Admin **projects** CRUD | Option B in SPEC; showcases-only slice shipped first (US-021) |
| Full **tags** model | Showcase `industry` / `use_case` fields cover MVP; dedicated tag tables later |
| Advanced **caching** | `force-dynamic` + `no-store` fetches for correct publish visibility; CDN/SWR later |

### Success criteria

- [x] At least two public AI Lab articles are published manually (seed + E2E publish flow).
- [x] At least two showcases are published (seed: Scopelytics, AI Interview System).
- [x] Public users can view only published content (API filters + E2E).
- [x] Admin publish/unpublish actions are authenticated and audit logged.

### Close-out verification

```text
cd frontend && npx -y react-doctor@latest . --verbose
python -m pytest backend/tests
cd frontend && npm run test && npm run typecheck && npm run lint && npm run build && npm run test:e2e
scripts/bin/harness-cli.exe story verify US-023
```

---

## MVP 2: AI-Assisted Blog Workflow

**Status: In progress** — core idea → outline → draft → technical review flow is implemented; polish and remaining contract items are still active.

Objective: add AI assistance while keeping humans in control.

Delivered:

- Blog idea creation and admin review API/UI.
- Structured outline generation from approved ideas.
- Draft writer generation from approved outlines.
- Technical review generation from approved drafts.
- Marketing metadata generation support.
- Human approve/reject controls for each generated stage.
- Regenerate affordances for rejected outline, draft, technical review, and marketing outputs.
- Basic queued/completed/error feedback after AI generation actions.
- Publish-from-approved-AI-flow bridge into blog posts (US-032).
- AI run metadata persistence (`ai_runs` table, recording wrapper).
- Durable Celery generation job tracking and admin polling (US-034).
- Claim extraction and evidence ledger with publish blocking (US-035).

Remaining (post-MVP 2 polish):

- Richer claim review UI and editor integration.
- Native Harness CLI integration for `ai_runs` / job queries.

---

## MVP 3: AI News from Official Sources

**Status: Implemented** (2026-06-03) — US-036 through US-041.

Objective: prove the AI News pipeline with lower-risk sources before X/Twitter.

Delivered:

- Admin news source registry with credibility base scores (US-036).
- RSS crawl, SSRF validation, and raw item storage (US-037).
- Async article extraction with Firecrawl/fake provider (US-038).
- URL canonicalization and exact URL/content-hash dedup (US-039).
- Heuristic multi-dimension scoring and admin review queue API (US-040).
- Publish approved items to public `/ai-news` feed (US-041).

Deferred (post-MVP 3):

- Public topic filtering on `/ai-news`.
- LLM-based scoring prompts and AI summary generation.
- GitHub/website crawl types beyond registry stubs.
- Dedicated admin review-queue UI (API endpoints only).
- `/ai-news/submit` (MVP 4).

---

## MVP 4: User-Submitted Links

**Status: Planned**

Objective: allow safe user/internal team link submission.

Features:

- `/ai-news/submit` form.
- URL validation, rate limiting, idempotency, and SSRF-protected async fetching.
- Duplicate detection and AI review.
- Human approval before publish.

---

## MVP 5: X/Twitter Intelligence

**Status: Blocked** — entry criteria not met.

Objective: add social intelligence only after provider strategy is accepted.

Entry criteria:

- Provider strategy chosen.
- Source account and keyword list defined.
- Required and nullable fields documented.
- Rate limits, budget, provider terms, fallback behavior, and risk owner agreed.
