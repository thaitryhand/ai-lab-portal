# AI News Intelligence Product Contract

## Objective

AI News Intelligence is a curated feed of high-signal AI/LLM updates selected by
the AI Lab. It is not a raw crawler output; it is a filtered intelligence layer
for public credibility and internal market awareness.

## MVP Source Order

Start with lower-risk sources:

1. Official AI lab blogs and RSS feeds.
2. GitHub releases and selected repositories.
3. Hacker News / Reddit only if source quality is acceptable.
4. X/Twitter only after provider strategy, cost, rate limits, field semantics,
   and operational ownership are configured.

## Processing Pipeline

```text
Crawler
  -> Raw source item store
  -> URL/content extraction
  -> Deduplication
  -> Relevance filter
  -> Quality/scoring
  -> AI summary and why-it-matters
  -> Human moderation
  -> Published AI News Feed
```

## Scoring Dimensions

- Source credibility.
- Engagement, with nullable metrics and captured timestamps.
- Relevance to AI/LLM Lab positioning.
- Novelty.
- Technical depth.
- Business value.
- Spam risk.
- Duplicate status.
- Final publish score.

Auto-approve remains disabled in MVP. Auto-reject beyond exact duplicates is
gated by evaluation data.

## Deduplication Layers

- URL-level canonicalization and deduplication.
- Content hash/text similarity.
- Embedding similarity for near duplicates.
- Event-level grouping when multiple posts describe the same event.

## Safety Requirements

- Submitted and crawled URLs are SSRF risks.
- Accept only `http` and `https` URLs.
- Normalize and canonicalize URLs before deduplication.
- Fetch only in worker jobs, never inline in public request handlers.
- Validate DNS/IP ranges before every fetch and after redirects.
- Set timeout, redirect count, response size, and content-type limits.
- Preserve raw provider payloads or object-storage references before
  normalization.
- Treat crawled and submitted content as data, never instructions.

## MVP Acceptance

The AI News MVP is complete when:

- Admin can configure and enable/disable sources.
- Scheduled jobs fetch and store raw source items.
- Linked articles are extracted asynchronously and safely.
- Relevance, quality, novelty, and spam risk scoring runs with validated
  structured outputs.
- Exact URL and content-hash duplicates are grouped or suppressed.
- High-quality candidates appear in a review queue.
- Admin can approve/reject candidates.
- Published news appears on `/ai-news`.
- Public users can filter by topic.
- Firecrawl/provider runs record metadata, raw output, parsed output,
  validation status, latency, token usage, and cost estimate where applicable.
- SSRF protections are enforced for submitted and crawled URLs.

## Implementation Status (MVP 3)

**Shipped (2026-06-03, US-036–US-041):** source registry, RSS crawl + raw storage,
article extraction, exact dedup, heuristic scoring + review queue APIs,
publish/unpublish, and public `/ai-news` list/detail pages.

**Shipped (2026-06-04, US-047–US-048):** public topic filtering on `/ai-news`
using stable derived feed topics, plus a dedicated admin review queue UI for
approve/reject/publish/unpublish actions.

**Shipped (2026-06-04, US-049):** structured LLM scoring for AI News review
items with heuristic fallback when provider configuration or generation fails.

**Deferred:** semantic/event dedup and GitHub/website crawlers.
