# E15 Content Analytics & Insights

Add page view tracking, content performance analytics, related article recommendations, and CSV export capabilities to the AI Lab Portal.

## Motivation

The portal has 100+ implemented stories but zero analytics. We don't know:
- Which pages are most popular
- How visitors navigate the site
- Which content drives engagement
- Whether SEO improvements are working

This epic adds lightweight, privacy-respecting analytics using the existing Postgres database — no third-party services, no cookies, no ads.

## Stories

| Story | Scope | Depends On |
|---|---|---|
| **US-103** | Page view tracking: `page_views` table, `POST /api/page-view`, `usePageView()` hook | — |
| **US-104** | Analytics dashboard: trends chart, top content table, referrer breakdown, summary cards | US-103 |
| **US-105** | Related article recommendations on blog detail page | US-103 (view count tiebreaker) |
| **US-106** | Event tracking: `events` table, share/click tracking, CSV export | US-103, US-104 |

## Architecture

```text
Frontend: usePageView() hook      trackEvent() helper
    |                                    |
    v                                    v
POST /api/page-view              POST /api/track-event
    |                                    |
    v                                    v
PageViewRepository               EventRepository
    |                                    |
    v                                    v
[page_views table]               [events table]
    |                                    |
    +--- GET /admin/analytics/* ---------+
              |
              v
         Admin Dashboard
    (CSS charts, stat cards)
              |
              v
    CSV Export endpoints
```

## Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Storage | Postgres (existing) | No new infrastructure, privacy-first |
| Tracking | Anonymous + session-only | No cookies, no GDPR concerns |
| IP storage | SHA-256 hashed | Privacy by design |
| Charts | CSS bar charts (no library) | Zero dependencies, sufficient for simple metrics |
| Rate limiting | Client-side throttle | Simple, prevents accidental spam |
| Export | CSV | Universal format, no dependencies |

## Exit Criteria

- [ ] Page views tracked on all public pages
- [ ] Admin analytics dashboard shows real data
- [ ] Related articles show on blog posts
- [ ] Share/click events tracked and exportable as CSV
- [ ] No third-party analytics services added
