# US-106 Event Tracking and CSV Export

## Status

planned

## Lane

normal

## Intake

#115 — Content Analytics & Insights

## Product Contract

Add custom event tracking (clicks, shares, comments) alongside page views, and provide CSV export capability for all analytics data.

## Epic

E15-content-analytics

## Affected Docs

- `backend/app/events.py` — new module (events table, model, repo, routes)
- `backend/app/database.py` — add `events` table definition
- `backend/app/main.py` — wire routes
- `backend/app/analytics_api.py` — add export endpoints
- `backend/migrations/versions/` — new migration for `events` table
- `frontend/lib/track-event.ts` — new event tracking utility
- Site components: wire share buttons, comment events, external link clicks

## Acceptance Criteria

1. `events` table stores: `id`, `path`, `event_type` (click|share|comment|scroll), `event_metadata` (JSONB), `session_id`, `created_at`
2. `POST /api/track-event` public endpoint: `{ path, event_type, metadata? }` — no auth, no API key
3. `trackEvent(eventType, metadata?)` utility function for frontend components
4. Pre-wired events: share buttons (Twitter, LinkedIn), external link clicks, comment submission
5. `GET /admin/analytics/export/views?from=...&to=...` returns CSV of page views
6. `GET /admin/analytics/export/events?from=...&to=...&type=...` returns CSV of events (optionally filtered by type)
7. CSV download triggers browser download with proper filename
8. Admin dashboard (US-104) shows key event counts in summary cards
9. Frontend typecheck, lint, and build pass

## Non-Goals

- No real-time event processing
- No event funnel analysis
- No retention/cohort analysis

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | EventRepository CRUD tests |
| Integration | `POST /api/track-event` stores event; CSV export returns valid CSV |
| E2E | Playwright: trigger share event, verify via admin export |
| Platform | Migration runs cleanly |
| Release | `cd frontend && npm run typecheck && npm run lint && npm run build` |
