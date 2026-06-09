# US-103 Page View Tracking

## Status

planned

## Lane

normal

## Intake

#115 — Content Analytics & Insights

## Product Contract

Add anonymous page view tracking to the public-facing site. Store page views in
a dedicated `page_views` Postgres table, expose a lightweight public API
endpoint for recording views, and provide a React hook that automatically
tracks page navigation events.

## Epic

E15-content-analytics

## Affected Docs

- `backend/app/page_views.py` — new module (model + repo + routes)
- `backend/app/database.py` — add `page_views` table definition
- `backend/app/main.py` — wire routes
- `backend/migrations/versions/` — new migration for `page_views` table
- `frontend/lib/use-page-view.ts` — new React hook
- `frontend/app/layout.tsx` — mount hook in root layout

## Acceptance Criteria

1. `page_views` table stores: `id`, `path`, `referrer`, `user_agent`, `ip_address` (hashed), `session_id`, `viewport_width`, `viewport_height`, `created_at`
2. `POST /api/page-view` public endpoint accepts view event with minimal payload (path, referrer, session_id, viewport) — no auth required, no API key
3. Rate limiting: max 1 request per path per session per 30 seconds (client-side throttle)
4. `usePageView()` React hook auto-tracks on route change (Next.js `usePathname`)
5. IP addresses are hashed (SHA-256) before storage — no raw IP storage
6. Hook is mounted in root layout, covers all public pages
7. Admin pages are NOT tracked by default
8. Frontend typecheck, lint, and build pass

## Non-Goals

- No user identification or cookies (anonymous only)
- No ad-tech or third-party analytics services
- No real-time aggregation or dashboard — that's US-104
- No click/event tracking — that's US-106

## Design Notes

- API endpoint is intentionally simple: `{ path: string, referrer?: string, session_id: string, viewport_width?: number, viewport_height?: number }`
- Session ID generated once per browser tab via `crypto.randomUUID()` stored in `sessionStorage`
- Client-side throttle: track last tracked path+timestamp in a module-level Map, skip if <30s since last view for same path
- Backend uses FastAPI `BackgroundTasks` for async write — don't block response
- Repository pattern: `PageViewRepository` ABC with `InMemoryPageViewRepository` (test) and `PostgresPageViewRepository`
- IP extraction via `request.client.host`, SHA-256 hashed before storage

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | `PageViewRepository` CRUD tests (in-memory + postgres) |
| Integration | `POST /api/page-view` returns 200, stores record |
| E2E | Playwright: navigate pages, verify views stored via admin API |
| Platform | Migration runs cleanly |
| Release | `cd frontend && npm run typecheck && npm run lint && npm run build` |

## Harness Delta

- New module: `backend/app/page_views.py`
- New migration for `page_views` table
- New frontend hook: `frontend/lib/use-page-view.ts`
- Updated: `backend/app/database.py`, `backend/app/main.py`, `frontend/app/layout.tsx`
