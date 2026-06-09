# US-104 Analytics Dashboard

## Status

planned

## Lane

normal

## Intake

#115 — Content Analytics & Insights

## Product Contract

Build an admin analytics dashboard showing page view trends, top-performing content, and key metrics over configurable time ranges. Uses data from the `page_views` table (US-103).

## Epic

E15-content-analytics

## Affected Docs

- `backend/app/analytics_api.py` — new analytics aggregation API
- `backend/app/main.py` — wire routes
- `frontend/app/admin/analytics/page.tsx` — new analytics dashboard page
- `frontend/components/admin/analytics/` — chart components

## Acceptance Criteria

1. Admin dashboard at `/admin/analytics` shows:
   - **Summary cards**: Total views (today, 7d, 30d, all-time), unique visitors, pages/session
   - **Views over time**: Bar/line chart of daily views for selected period (7d, 30d, 90d)
   - **Top content**: Table of most-viewed pages with view count, trend (up/down)
   - **Referrer breakdown**: Top referrers with view count
2. `GET /admin/analytics/summary` returns aggregated stats
3. `GET /admin/analytics/top-content?days=30&limit=10` returns top pages
4. `GET /admin/analytics/trends?days=30` returns daily view counts
5. Date range picker (7d, 30d, 90d) updates all charts
6. Charts are CSS-based (no external chart library) — bar charts and stat cards
7. Responsive layout works on desktop and tablet
8. Frontend typecheck, lint, and build pass

## Non-Goals

- No real-time updates (static data on page load)
- No drill-down into individual page analytics
- No export — that's US-106
- No user-level analytics

## Design Notes

- All aggregation queries use COUNT + GROUP BY on the `page_views` table
- Pre-aggregation via materialized view is deferred until performance requires it
- CSS bar charts: simple percent-width div bars, no external dependency
- Trend arrows: simple CSS-up/down triangles with percentage change
- Sidebar nav link under existing admin navigation

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Analytics aggregation queries return correct counts |
| Integration | `GET /admin/analytics/*` endpoints return valid JSON |
| E2E | Playwright: verify stat cards render with non-zero values after page views |
| Platform | N/A |
| Release | `cd frontend && npm run typecheck && npm run lint && npm run build` |
