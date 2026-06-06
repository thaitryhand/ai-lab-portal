# US-074 SEO Foundation

## Status

implemented

## Lane

normal

## Intake

Retroactive — harness hygiene sync (2026-06-06).

## Product Contract

Public pages need crawlable SEO metadata, sitemap, and robots directives so
search engines and social platforms can index and preview AI Lab content.

## Acceptance Criteria

1. Root and key public routes expose appropriate `<title>`, description, and Open Graph metadata.
2. `sitemap.xml` lists published public URLs (blog, showcases, ai-news, projects).
3. `robots.txt` allows indexing of public surfaces and blocks admin routes.
4. Article pages include share-friendly metadata and improved SEO fields.
5. Frontend typecheck, lint, and build pass.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | N/A |
| Integration | N/A |
| E2E | Smoke checks for metadata routes |
| Platform | N/A |
| Release | `cd frontend && npm run typecheck && npm run lint && npm run build` |

## Evidence

- Commit `a75c19d` — seo: metadata, sitemap.xml, robots.txt
- Commit `839046d` — feat(public): improve article seo and sharing
