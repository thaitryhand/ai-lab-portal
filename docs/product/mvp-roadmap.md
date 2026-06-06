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
| MVP 2 | AI-assisted blog | **Implemented** | US-025–US-035, US-043 |
| MVP 3 | AI News (official sources) | **Implemented** | US-036–US-041 |
| MVP 4 | User-submitted links | **Implemented** | US-044–US-046 |
| MVP 5 | X/Twitter intelligence | Fake provider implemented; real Apify blocked on budget/terms | US-053–057 |
| Post-MVP | Blog social, contact, notifications, projects, polish, SEO, search | **Implemented** | US-058–083 |

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

**Status: Implemented** (2026-06-03) — US-025 through US-035.

Objective: add AI assistance while keeping humans in control.

Delivered:

- Blog idea creation and admin review API/UI.
- Structured outline, draft, and technical review generation.
- Marketing metadata generation support.
- Human approve/reject controls and regenerate affordances.
- Publish-from-approved-AI-flow bridge into blog posts (US-032).
- AI run metadata persistence (`ai_runs`, US-033).
- Durable Celery generation job tracking and admin polling (US-034).
- Claim extraction and evidence ledger with publish blocking (US-035).

Deferred (post-MVP 2):

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

Post-MVP 3 shipped:

- Public topic filtering on `/ai-news` (US-047).
- Dedicated admin review-queue UI for approve/reject/publish/unpublish actions (US-048).
- LLM-based scoring prompts and AI summary generation with heuristic fallback (US-049).

Deferred:

- GitHub/website crawl types beyond registry stubs.

---

## MVP 4: User-Submitted Links

**Status: Implemented** (2026-06-03) — US-044 through US-046.

Objective: allow safe user/internal team link submission.

Delivered:

- Public `/ai-news/submit` form and `POST /public/submitted-links` (US-044).
- SSRF URL validation, canonical idempotency, and rate limiting (US-044).
- Admin submitted-link list/get/process APIs (US-044).
- Async `news.process_submitted_link` worker (US-044).
- Pipeline merge: raw item → extract → dedup → score → review (US-045).
- Submission linkage via `raw_item_id` / `review_item_id` and `in_review` status (US-045).

Deferred (post-MVP 4):

- AI classification output on submissions.
- Dedicated admin review UI for submitted links.

---

## MVP 5: X/Twitter Intelligence

**Status: Fake provider implemented; real Apify blocked on human gate** (2026-06-04).

Objective: evaluate social intelligence as a future AI News source class only after provider, data, terms, cost, and moderation risks are accepted.

### Delivered (fake provider path)

| Story | Capability |
| --- | --- |
| US-051–052 | Planning stub and provider research (Apify-first strategy) |
| US-053–054 | Source contract, fake fixtures, AI social link filter |
| US-055 | X/Twitter ingestion spike with fake provider |
| US-056 | Social item scoring calibration (author credibility, engagement) |
| US-057 | Admin review affordances for social context |

### Entry criteria for real provider (not yet met)

- Provider strategy chosen and documented in a durable decision record. ✓ (US-052)
- Source account and keyword list defined.
- Required and nullable fields documented, including engagement and author metadata semantics. ✓ (US-053)
- Rate limits, budget, provider terms, fallback behavior, and risk owner agreed. **Blocked — backlog #4**
- Moderation, attribution, storage, and display policy accepted.
- Fake-provider validation plan exists before any real provider implementation. ✓

Non-goal until human gate clears: do not call real Apify or X/Twitter APIs in production.

---

## Post-MVP: Blog Social, Platform Polish, and Content Ops

**Status: Implemented** (2026-06-04 through 2026-06-06) — US-058 through US-083.

Objective: ship credible public-facing blog social features, complete deferred platform slices (contact, notifications, projects, admin dashboard), and polish UX/SEO for launch readiness.

### Delivered

| Area | Stories | Notes |
| --- | --- | --- |
| Blog social | US-058–061 | Public blog creation, tags, threaded comments, following/feeds |
| Contact | US-062–063 | Backend API + public `/contact` form |
| Notifications | US-064–065 | Backend API + notification bell UI |
| Projects | US-066–068 | Backend CRUD + admin UI + public `/projects` pages |
| UI/UX polish | US-069–071 | Loading skeletons, micro-interactions, responsive/hamburger nav |
| Admin dashboard | US-072–073 | Unified stats API + stat cards UI |
| SEO foundation | US-074 | Metadata, sitemap.xml, robots.txt, article sharing |
| Blog UX | US-075 | Reading time, RSS, infinite scroll, related posts |
| Blog media | US-076 | Image upload in editor, Docker volume persistence |
| Public profile | US-077 | Avatar/cover uploads, profile redesign, header avatar sync |
| Blog social hardening | US-078 | Comment reactions, bookmarks, TipTap comment editor |
| Admin polish | US-079 | Health status widget, dashboard comment stats, blog search |
| Home redesign | US-080 | Editorial landing sections, spacing rhythm |
| Auth polish | US-081 | Session refresh, password visibility, login/register redesign |
| Search | US-082 | ILIKE filtering in blog and AI news repositories |
| Content ops | US-083 | Editorial seed scripts, expanded E2E proof coverage |

### Still deferred (not story-tracked)

| Item | Reason |
| --- | --- |
| Real Apify X/Twitter ingestion | Budget/terms gate (backlog #4) |
| Admin submitted-links review UI | API complete; UI deferred |
| GitHub/website crawl beyond RSS | Registry stubs only |
| Advanced caching / CDN | Correctness-first `no-store` fetches |
| Richer claim review UI | Post-MVP 2 deferral |
