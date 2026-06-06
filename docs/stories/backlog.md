# Story Backlog

This backlog is seeded from `SPEC.md` and should be expanded only as work is
selected. Do not create every possible story packet up front.

Create story packets when the work is selected or when a product decision needs
a durable place to land.

## Candidate Epics

| Epic | Description | Status |
| --- | --- | --- |
| E00 Foundation | Runtime scaffold, health, migrations, Redis/Celery, structured logs, local orchestration | implemented |
| E01 Manual CMS and Public Pages | Public AI Lab/showcase/blog pages plus manual admin publishing workflow | implemented |
| E02 AI-Assisted Blog Workflow | Blog idea, outline, draft, review, marketing metadata, and prompt/AI run tracking | implemented (MVP 2) |
| E03 AI News Official Sources | RSS/official/GitHub source ingestion, extraction, dedup, scoring, review queue, public feed | implemented (MVP 3) |
| E04 User-Submitted Links | Safe link submission, SSRF-protected async fetch, duplicate detection, human approval | implemented (MVP 4) |
| E05 X/Twitter Intelligence | Social ingestion after provider strategy and risk ownership are accepted | fake provider implemented (US-053–057); real Apify blocked on budget/terms (#4) |
| E06 Contact | Contact form public page and admin message review | implemented |
| E07 Notifications | User notification system for follows and comment replies | implemented |
| E08 Projects | Company projects CRUD and public pages | implemented |
| E09 UI/UX Polish | Loading states, micro-interactions, responsive improvements | implemented |
| E10 Admin Dashboard | Stats API and stat cards for admin dashboard | implemented |
| E11 Post-MVP Polish | SEO, blog UX, profile, social hardening, admin/home redesign, auth polish, search, content ops | implemented (US-074–083) |

## Selected Stories

| Story | Epic | Status |
| --- | --- | --- |
| `US-001` | E00 Foundation | implemented |
| `US-002` | E01 Auth | implemented |
| `US-003` | E01 Auth | implemented |
| `US-004` | E01 Auth | implemented |
| `US-009` | E01 Auth | implemented |
| `US-010` | E01 Auth | implemented |
| `US-005` | E02 Manual CMS | implemented |
| `US-006` | E02 Manual CMS | implemented |
| `US-007` | E02 Manual CMS | implemented |
| `US-008` | E02 Manual CMS | implemented |
| `US-011` | E02 Manual CMS | implemented |
| `US-012` | E02 Manual CMS | implemented |
| `US-013` | E02 Manual CMS | implemented |
| `US-014` | E02 Manual CMS | implemented |
| `US-015` | E02 Manual CMS | implemented |
| `US-016` | E02 Manual CMS | implemented |
| `US-017` | E02 Manual CMS | implemented |
| `US-018` | E02 Manual CMS | implemented |
| `US-019` | E02 Manual CMS | implemented |
| `US-020` | E02 Manual CMS | implemented |
| `US-021` | E02 Manual CMS | implemented |
| `US-022` | E02 Manual CMS | implemented |
| `US-023` | E02 Manual CMS | implemented |
| `US-024` | E00 Foundation | implemented |
| `US-025`–`US-031` | E03 AI Blog Agent | implemented |
| `US-032` | E03 AI Blog Agent | implemented |
| `US-033` | E03 AI Blog Agent | implemented |
| `US-034` | E03 AI Blog Agent | implemented |
| `US-035` | E03 AI Blog Agent | implemented |
| `US-036` | E04 AI News | implemented |
| `US-037` | E04 AI News | implemented |
| `US-038` | E04 AI News | implemented |
| `US-039` | E04 AI News | implemented |
| `US-040` | E04 AI News | implemented |
| `US-041` | E04 AI News | implemented |
| `US-042` | E04 AI News | implemented |
| `US-043` | E03 AI Blog Agent | implemented |
| `US-044` | E04 User-Submitted Links | implemented |
| `US-045` | E04 User-Submitted Links | implemented |
| `US-046` | E04 User-Submitted Links | implemented |
| `US-051` | E05 X/Twitter | implemented (planning stub) |
| `US-052` | E05 X/Twitter | implemented (provider research) |
| `US-053` | E05 X/Twitter | implemented |
| `US-054` | E05 X/Twitter | implemented |
| `US-055` | E05 X/Twitter | implemented |
| `US-056` | E05 X/Twitter | implemented |
| `US-057` | E05 X/Twitter | implemented |
| `US-058` | Blog creation from public page | implemented |
| `US-059` | Blog tag picker and rich taxonomy | implemented |
| `US-060` | Threaded blog comments | implemented |
| `US-061` | User following and blog feeds | implemented |
| `US-062` | E06 Contact | implemented |
| `US-063` | E06 Contact | implemented |
| `US-064` | E07 Notifications | implemented |
| `US-065` | E07 Notifications | implemented |
| `US-066` | E08 Projects | implemented |
| `US-067` | E08 Projects | implemented |
| `US-068` | E08 Projects | implemented |
| `US-069` | E09 UI/UX Polish | implemented |
| `US-070` | E09 UI/UX Polish | implemented |
| `US-071` | E09 UI/UX Polish | implemented |
| `US-072` | E10 Admin Dashboard | implemented |
| `US-073` | E10 Admin Dashboard | implemented |
| `US-074` | E11 Post-MVP Polish | implemented |
| `US-075` | E11 Post-MVP Polish | implemented |
| `US-076` | E11 Post-MVP Polish | implemented |
| `US-077` | E11 Post-MVP Polish | implemented |
| `US-078` | E11 Post-MVP Polish | implemented |
| `US-079` | E11 Post-MVP Polish | implemented |
| `US-080` | E11 Post-MVP Polish | implemented |
| `US-081` | E11 Post-MVP Polish | implemented |
| `US-082` | E11 Post-MVP Polish | implemented |
| `US-083` | E11 Post-MVP Polish | implemented |

## Open / Deferred (not yet story-tracked)

| Item | Notes |
| --- | --- |
| MVP5 real Apify provider | Blocked on budget/terms decision (backlog #4) |
| Admin submitted-links review UI | API exists; dedicated UI deferred from MVP 4 |
| GitHub/website crawl types | Registry stubs only; beyond RSS in MVP 3 |
| Advanced caching / CDN | `force-dynamic` + `no-store` for publish correctness |
| Richer claim review UI | Deferred from MVP 2 |
