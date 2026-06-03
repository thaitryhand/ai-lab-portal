# Test Matrix

Maps MVP 1 product behavior to proof layers. Update when story contracts change.

## Status Values

| Status | Meaning |
| --- | --- | --- |
| planned | Accepted as intended behavior, not implemented |
| in_progress | Actively being built |
| implemented | Implemented and proof exists |
| changed | Contract changed after earlier implementation |
| retired | No longer part of the product contract |

## Matrix (MVP 1 focus)

| Story | Contract | Unit | Integration | E2E | Platform | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| US-005–006 | Published blog read model + admin blog API | yes | yes | no | no | implemented | `backend/tests/test_blog_public.py`, `test_admin_blog.py` |
| US-011–017 | Admin blog list, editor, publish from list | no | yes | yes | no | implemented | `frontend/tests/e2e/shell.spec.ts` |
| US-019–020 | CMS pending states + shadcn admin UI | no | no | yes | no | implemented | story validation US-019/020 |
| US-021 | Showcases API + public/admin + `/lab` | yes | yes | yes | no | implemented | `test_showcase_public.py`, `test_admin_showcase.py`, E2E showcase/lab |
| US-022 | Public shell polish, SEO metadata, theme tokens | no | no | yes | no | implemented | E2E home nav, `createPublicMetadata` |
| US-023 | MVP 1 close-out, React Doctor, roadmap status | no | no | yes | no | implemented | React Doctor 100/100, `mvp-roadmap.md` |
| US-032 | Publish approved blog idea to CMS blog post | yes | yes | no | no | implemented | `backend/tests/test_blog_publish.py` |
| US-033 | AI run metadata (`ai_runs`) | yes | yes | no | no | implemented | `backend/tests/test_blog_observability.py` (`-k recording`) |
| US-034 | Celery generation job polling | yes | yes | no | no | implemented | `backend/tests/test_blog_observability.py` (`-k generation_job`) |
| US-035 | Claim evidence ledger + publish guard | yes | yes | no | no | implemented | `backend/tests/test_blog_observability.py` (`-k claim`) |
| US-036 | Admin news source registry | yes | yes | no | no | implemented | `backend/tests/test_news_sources.py` |
| US-037 | RSS crawl + raw item storage | yes | yes | no | no | implemented | `backend/tests/test_news_crawl.py` |
| US-038 | Article extraction from raw news items | yes | yes | no | no | implemented | `backend/tests/test_news_extraction.py` |
| US-039 | URL canonicalization + exact deduplication | yes | yes | no | no | implemented | `backend/tests/test_news_dedup.py` |
| US-040 | Heuristic scoring + review queue | yes | yes | no | no | implemented | `backend/tests/test_news_scoring.py` |
| US-041 | Public `/ai-news` feed | yes | yes | yes | no | implemented | `backend/tests/test_news_publish.py` |
| US-042 | MVP3 AI News closeout | yes | yes | yes | no | implemented | `backend/tests/test_news_*.py` (combined) |

## Evidence Rules

- Unit proof covers pure domain and application rules.
- Integration proof covers backend enforcement, data integrity, provider behavior, jobs, or service contracts.
- E2E proof covers user-visible browser flows.
- Platform proof covers shell, deployment, or runtime behavior not proven in lower layers.
