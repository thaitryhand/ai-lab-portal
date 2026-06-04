# 0008 X/Twitter Provider Strategy

Date: 2026-06-04

## Status

Proposed

## Context

MVP 5 is blocked until the X/Twitter provider, terms, data contract, cost, and moderation risks are accepted. The product need is stronger than GitHub/website crawling because X/Twitter carries earlier signals, launch chatter, founder/researcher commentary, and links that may not appear in official feeds.

Current AI News infrastructure already supports raw item storage, extraction, deduplication, LLM/heuristic scoring, human review, and public publishing. The missing MVP 5 boundary is the social-source provider and a first-pass AI filter that decides whether a post/link should enter the existing AI News pipeline.

Research inputs:

- Firecrawl scrape endpoint: `https://docs.firecrawl.dev/api-reference/endpoint/scrape`
- Apify Twitter Scraper by Maxime Dupré: `https://apify.com/maximedupre/twitter-scraper/api/openapi`
- Apify Xquik X Tweet Scraper: `https://apify.com/xquik/x-tweet-scraper/input-schema`

## Decision

Use **Apify as the preferred MVP 5 research/implementation candidate**, with **Xquik X Tweet Scraper** as the likely first trial actor and **Maxime Dupré Twitter Scraper** as the backup comparison actor.

Use **Firecrawl only for linked article/page extraction after the AI filter accepts a post/link**, not as the primary X/Twitter discovery provider.

Do not start production ingestion until legal/terms, storage/display policy, budget ceiling, and source scope are accepted. The first implementation story should use fake provider fixtures matching Apify-like output before any real Apify call.

## Alternatives Considered

1. **Firecrawl primary X/Twitter discovery**
   - Firecrawl is strong for scraping a single URL or batch of URLs and can return markdown/html/links/screenshots/json; it supports browser actions, proxy modes, caching controls, and rate/payment errors.
   - It is not documented as an X/Twitter search/profile/list provider with stable social fields like engagement metrics, author identity, quoted-post context, and reply relationships.
   - Good fit: scrape links found inside accepted posts, or enrich linked articles after social filtering.

2. **Apify Maxime Dupré Twitter Scraper**
   - Strong fit for topic/account search. It supports phrase/word/account/mention/hashtag/list/date/language/engagement filters, latest/top search ordering, original/quote/reply toggles, and partial-result behavior.
   - Output fields include post ID/URL/text/timestamp, author handle/display/avatar, likes/reposts/replies/views/bookmarks, media, hashtags, quoted-post fields, and reply context.
   - Listed pricing: from $0.40 per 1,000 scraped tweets.
   - Tradeoff: community actor; reliability and terms still require review.

3. **Apify Xquik X Tweet Scraper**
   - Strongest first-trial fit for MVP 5 because it supports profiles, search URLs, lists, tweet IDs, advanced search syntax, Latest/Top/Latest+Top, deduplication, diagnostics, and clear low listed price.
   - Output fields include tweet ID/text/timestamp, engagement metrics, language, URL, author profile, media, entities, quote/reply/thread fields, and conversation ID.
   - Listed pricing: $0.15 per 1,000 tweets, with platform usage included per actor docs.
   - Tradeoff: third-party/community actor and claims still require a small real sample run before production trust.

4. **Official X API**
   - Best terms posture but likely slower to procure and potentially more expensive/constrained for discovery. Keep as long-term compliance option if Apify terms are rejected.

## Consequences

Positive:

- MVP 5 can move toward high-signal social discovery without waiting for official X API procurement.
- Apify outputs map well to the existing AI News scoring dimensions: source credibility, engagement, novelty, spam risk, author/source metadata, and source URLs.
- Firecrawl remains useful in its proven role: linked article extraction after a post/link is selected.

Tradeoffs:

- Third-party scraper terms, storage/redisplay rules, and personal-data exposure need explicit owner approval.
- Community actor schemas may change; normalized fixtures and provider-adapter tests are mandatory.
- X/Twitter UI/anti-bot changes may break scrapers; provider failures must degrade to queued/failed jobs, never public request failures.

## Follow-Up

- Add an MVP 5 source contract story using fake Apify-style fixtures.
- Define an AI social link filter schema before ingestion: `should_ingest`, `reason`, `topic`, `priority`, `risk_flags`, `urls_to_extract`, and `requires_human_review`.
- Run a tiny paid Apify sample only after budget/terms owner approval.
- Keep Firecrawl as the linked-page extractor for accepted URLs.
- Record a final Accepted/Superseded decision after the sample run and legal/terms review.
