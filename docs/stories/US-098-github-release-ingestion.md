# US-098 GitHub Release Ingestion for AI News Pipeline

## Status

implemented

## Lane

normal

## Intake

E12 AI Blog Agent v2 — GitHub release ingestion as a new source type for AI News (2026-06-06).

## Product Contract

AI News pipeline can ingest GitHub releases as news items. `GitHubReleaseProvider` with both fake and real modes. URL parser handles owner/repo, full URL, and releases URL formats. Ingestion produces `ParsedFeedItems`, respects dedup, and updates `last_crawled_at`. Due-source runner filters only `github` source type, skipping not-yet-due sources.

## Acceptance Criteria

1. GitHubReleaseProvider with fake/real modes.
2. URL parser handles: owner/repo, full URL, releases URL.
3. Ingestion produces ParsedFeedItems compatible with existing pipeline.
4. Dedup respects existing items (URL + content hash).
5. Due-source runner filters `github` source type only.
6. Default sources: `openai/openai-agents-python` and `langchain-ai/langchain`.

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | Provider URL parsing, item production tests |
| Integration | 14/14 tests in `test_news_github_ingest.py` |
| E2E | N/A |
| Platform | N/A |
| Release | Full backend suite 306/306 pass |

## Evidence

- `backend/app/news/providers/github.py` — GitHub release provider
- `backend/tests/test_news_github_ingest.py` — 14 integration tests
- Default sources configured in source registry
