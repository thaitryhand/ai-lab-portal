# E05 X/Twitter Intelligence Planning Stub

## Status

blocked — entry criteria only

## Objective

Evaluate whether X/Twitter intelligence should become the next AI News source class, and define the minimum governance, provider, data, cost, and validation requirements before implementation starts.

This is a planning stub only. It does not authorize crawler, API, schema, queue, or UI implementation.

## Context

MVP 3 and post-MVP enhancements have already shipped lower-risk AI News capabilities:

- Official-source ingestion, extraction, exact deduplication, scoring, review, and public publish flow.
- Public topic filtering on `/ai-news`.
- Dedicated admin AI News review UI.
- Structured LLM scoring with heuristic fallback.
- User-submitted links feeding the same review pipeline.

X/Twitter remains higher risk because provider access, terms, rate limits, paid API cost, field semantics, and operational ownership are not yet accepted.

Provider research is captured in `docs/decisions/0008-x-twitter-provider-strategy.md`. Current proposed direction: Apify for X/Twitter discovery, Firecrawl only for linked-page extraction after an AI filter accepts a post/link.

## Entry Criteria

Implementation can start only after all criteria are true:

1. **Provider strategy chosen**
   - Proposed: Apify Xquik X Tweet Scraper as first trial actor; Maxime Dupré Twitter Scraper as backup actor; Firecrawl for accepted linked-page extraction only.
   - Before implementation, accept or revise `docs/decisions/0008-x-twitter-provider-strategy.md`.
   - Document terms-of-service constraints and allowed storage/redisplay behavior.

2. **Source scope defined**
   - Initial account list, keyword list, language scope, and inclusion/exclusion rules are approved.
   - Risk owner accepts that social data has higher spam, impersonation, and context-collapse risk than official RSS/blog sources.

3. **Data contract documented**
   - Required fields, nullable fields, timestamp semantics, engagement metrics, author metadata, URL references, and raw payload retention are documented.
   - Behavior is defined for deleted/private/unavailable posts.

4. **Budget and rate limits accepted**
   - API cost ceiling, rate-limit behavior, crawl frequency, backoff, and quota-exhaustion fallback are agreed.
   - No synchronous public/admin request may call the provider.

5. **Moderation and publish policy accepted**
   - X/Twitter items enter review as candidates only; no auto-publish.
   - Human review remains required before public display.
   - Attribution and source-link rules are defined.

6. **Validation plan exists**
   - Fake provider fixtures cover ingestion and scoring without real API calls.
   - Integration tests cover quota exhaustion, malformed payloads, duplicate links, and unavailable posts.
   - Story verify command is defined before implementation.

## AI Social Link Filter Contract (Draft)

The first social-specific AI step should run before article extraction. It decides whether a post/link is worth entering the existing AI News pipeline.

Input:

- Normalized social post fields: `post_id`, `post_url`, `post_text`, `created_at`, `author_handle`, `author_display_name`, `engagement_metrics`, `lang`, `quoted_post_text`, `reply_context`, `entities.urls`.
- Source scope metadata: matched account/list/search term, crawl run id, provider name, provider actor/version.
- Product preference: AI/LLM relevance, practical engineering signal, credible source, public-client usefulness, avoid hype/spam/drama.

Structured output:

```text
should_ingest: boolean
reason: string
topic: models | agents | research | policy | infrastructure | product | funding | security | general
priority: low | medium | high
risk_flags: string[]
urls_to_extract: string[]
requires_human_review: boolean
```

Rules:

- `should_ingest=false` for pure memes, personal drama, engagement bait, vague hype, unsupported rumors, or posts with no AI/LLM relevance.
- `urls_to_extract` must contain only http/https URLs found in the post/entities; extraction still uses the existing SSRF-safe worker path.
- `requires_human_review=true` for every accepted social item in MVP 5.
- The filter never publishes content and never bypasses review.

## Non-goals

- Do not implement provider calls in this stub.
- Do not add database migrations in this stub.
- Do not add X/Twitter UI surfaces in this stub.
- Do not scrape X/Twitter without an accepted provider/terms decision.
- Do not auto-publish social items.
- Do not build semantic/event deduplication as part of the first X/Twitter slice unless explicitly re-scoped.

## Candidate Stories

These are candidates, not approved implementation stories:

1. **US-052 Provider strategy acceptance / sample-run approval**
   - Accept or revise `docs/decisions/0008-x-twitter-provider-strategy.md`, name budget/terms owner, and approve or reject a tiny Apify sample run.

2. **US-053 X/Twitter source contract and fake fixtures**
   - Define source config shape, normalized raw item contract, Apify-like fake provider fixtures, and no-real-provider tests.

3. **US-054 AI social link filter contract**
   - Define structured output for `should_ingest`, `reason`, `topic`, `priority`, `risk_flags`, `urls_to_extract`, and `requires_human_review`.

4. **US-055 X/Twitter ingestion spike behind fake provider**
   - Add ingestion path using fake provider only, with no real provider calls.

5. **US-056 Social item scoring calibration**
   - Tune scoring dimensions for social signals with nullable engagement metrics and spam/impersonation risk.

6. **US-057 Admin review affordances for social context**
   - Show author, source post URL, engagement metadata, provider run metadata, and risk badges in the existing admin review UI.

## Blockers / Open Questions

- Will the team accept the proposed Apify-first provider strategy, or require official X API?
- Are we allowed to store raw post payloads, author metadata, and engagement metrics?
- Are we allowed to display excerpts, summaries, or only source links?
- What is the first approved account/keyword list?
- Who owns false-positive, misinformation, impersonation, and takedown review?
- What monthly spend ceiling and quota-exhaustion behavior are acceptable?
- Which first-run source scope is approved: account handles, search terms, X list, tweet URLs, or a mix?
- Should the first sample use Xquik ($0.15/1K listed) or Maxime Dupré ($0.40/1K listed) actor?

## Exit Criteria for This Stub

This stub is complete when it is referenced from the roadmap and the Harness trace records that no MVP 5 implementation was started.
