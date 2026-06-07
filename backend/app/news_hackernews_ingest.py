"""Hacker News story ingestion for the AI News pipeline.

Fetches top/new stories from the Hacker News Firebase API (free, no auth)
and converts them into ``ParsedFeedItem`` objects for the existing news pipeline.

Follows the same pattern as ``news_github_ingest.py``.

Firebase API: https://hacker-news.firebaseio.com/v0/
No API key needed. Rate limit: generous, undocumented.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from backend.app.news_crawl import ParsedFeedItem

if TYPE_CHECKING:
    from backend.app.news_crawl import NewsRawItemRepository
    from backend.app.news_sources import NewsSource, NewsSourceRepository

# ─── Fixture data for tests / dev ─────────────────────────────────────────

HN_FIXTURE_STORIES: list[dict[str, Any]] = [
    {
        "id": 48432199,
        "title": "The 29th IOCCC 2025 Winners",
        "url": "https://www.ioccc.org/2025/",
        "score": 208,
        "by": "matt_d",
        "time": 1780811274,
        "descendants": 51,
        "type": "story",
    },
    {
        "id": 48431000,
        "title": "Show HN: A new open-source AI agent framework",
        "url": "https://github.com/example/ai-agent-framework",
        "score": 156,
        "by": "ai_dev",
        "time": 1780809600,
        "descendants": 34,
        "type": "story",
    },
    {
        "id": 48429888,
        "title": "GPT-5 training infrastructure details",
        "url": "https://example.com/gpt5-infra",
        "score": 312,
        "by": "ml_researcher",
        "time": 1780808000,
        "descendants": 89,
        "type": "story",
    },
    {
        "id": 48427777,
        "title": "Ask HN: Best resources for learning LLM agents?",
        "url": "",
        "score": 45,
        "by": "learner42",
        "time": 1780806000,
        "descendants": 23,
        "type": "ask",
    },
]


# ─── Result type ──────────────────────────────────────────────────────────


@dataclass
class HackerNewsIngestionResult:
    """Outcome of one Hacker News source ingestion run."""

    source_id: str = ""
    stories_seen: int = 0
    items_stored: int = 0
    api_calls: int = 0
    errors: list[str] = field(default_factory=list)

    def model_dump(self) -> dict:
        return {
            "source_id": self.source_id,
            "stories_seen": self.stories_seen,
            "items_stored": self.items_stored,
            "api_calls": self.api_calls,
            "errors": self.errors,
        }


# ─── Provider ─────────────────────────────────────────────────────────────


HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
HN_FEED_TYPES = ("topstories", "newstories", "beststories")


class HackerNewsProvider:
    """Fetches stories from Hacker News Firebase API.

    The real provider uses the HN Firebase REST API (free, no auth).
    The fake provider returns fixture data for tests/dev.

    The ``url_or_identifier`` field stores the feed type:
    ``"topstories"``, ``"newstories"``, or ``"beststories"``.
    """

    def __init__(self, *, fake: bool = True) -> None:
        self._fake = fake
        self._api_base = HN_API_BASE

    def fetch_story_ids(self, feed_type: str) -> list[int]:
        """Fetch list of story IDs for a given feed type.

        Args:
            feed_type: ``"topstories"``, ``"newstories"``, or ``"beststories"``.

        Returns:
            List of up to 500 story IDs.
        """
        if self._fake:
            return [s["id"] for s in HN_FIXTURE_STORIES]

        import urllib.request

        url = f"{self._api_base}/{feed_type}.json"
        req = urllib.request.Request(url, headers={"User-Agent": "ai-lab-portal/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data: list[int] = json.loads(resp.read().decode())
            return data[:30]  # limit to 30 items per run

    def fetch_story(self, story_id: int) -> dict[str, Any] | None:
        """Fetch a single story item by ID.

        Returns:
            Story dict or ``None`` if not found.
        """
        if self._fake:
            for s in HN_FIXTURE_STORIES:
                if s["id"] == story_id:
                    return dict(s)
            return None

        import urllib.request

        url = f"{self._api_base}/item/{story_id}.json"
        req = urllib.request.Request(url, headers={"User-Agent": "ai-lab-portal/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data: dict[str, Any] | None = json.loads(resp.read().decode())
                return data
        except (urllib.error.HTTPError, urllib.error.URLError, OSError, json.JSONDecodeError):
            return None

    def fetch_stories(self, feed_type: str) -> list[dict[str, Any]]:
        """Fetch all stories for a feed type.

        Gets the ID list, then fetches each story.
        Filters to only items with ``type == "story"`` and a non-empty ``url``.
        """
        if self._fake:
            return [s for s in HN_FIXTURE_STORIES if s.get("type") == "story"]

        story_ids = self.fetch_story_ids(feed_type)
        stories: list[dict[str, Any]] = []
        api_calls = 1  # one call for the ID list

        for sid in story_ids:
            story = self.fetch_story(sid)
            api_calls += 1
            if story and story.get("type") == "story" and story.get("url"):
                stories.append(story)

        return stories


# ─── Converters ───────────────────────────────────────────────────────────


def _parse_hn_feed_type(url_or_identifier: str) -> str:
    """Normalize a Hacker News feed type identifier.

    Handles:
    - ``"topstories"``
    - ``"top"`` → ``"topstories"``
    - ``"new"`` → ``"newstories"``
    - ``"best"`` → ``"beststories"``
    """
    cleaned = url_or_identifier.strip().lower().rstrip("/")
    mapping = {
        "top": "topstories",
        "new": "newstories",
        "best": "beststories",
    }
    return mapping.get(cleaned, cleaned)


def _story_to_raw_item(
    story: dict[str, Any],
    *,
    source_id: str,
    fetched_at: datetime,
) -> ParsedFeedItem:
    """Convert a HN story dict to a ParsedFeedItem."""
    story_id = story.get("id", 0)
    external_id = f"hn_story_{story_id}"

    title = (story.get("title", "") or "")[:240]
    link_url = story.get("url", "") or f"https://news.ycombinator.com/item?id={story_id}"

    published_at = None
    raw_time = story.get("time")
    if raw_time:
        try:
            published_at = datetime.fromtimestamp(int(raw_time), tz=UTC)
        except (ValueError, TypeError, OSError):
            pass

    return ParsedFeedItem(
        external_id=external_id,
        title=title,
        link_url=link_url,
        published_at=published_at,
        raw_payload={
            "hn_story_id": story_id,
            "hn_score": story.get("score"),
            "hn_author": story.get("by"),
            "hn_descendants": story.get("descendants"),
            "hn_fetch_feed": source_id,
            "source_type": "hackernews",
        },
    )


# ─── Ingestion ────────────────────────────────────────────────────────────


def run_hackernews_fetch(
    source_id: str,
    *,
    sources: NewsSourceRepository,
    raw_items: NewsRawItemRepository,
    provider: HackerNewsProvider | None = None,
) -> HackerNewsIngestionResult:
    """Fetch stories for one HN source and store as raw items.

    Args:
        source_id: The news source ID to fetch.
        sources: NewsSourceRepository for source config lookup.
        raw_items: NewsRawItemRepository for storing fetched raw items.
        provider: Optional HackerNewsProvider (uses fake by default).

    Returns:
        HackerNewsIngestionResult with counts.
    """
    source = sources.get_by_id(source_id)
    if source is None:
        raise ValueError(f"HN source not found: {source_id}")
    if source.source_type != "hackernews":
        raise ValueError(f"Source {source_id} is not a hackernews source (type={source.source_type})")
    if not source.is_enabled:
        raise ValueError(f"Source {source_id} is disabled")

    feed_type = _parse_hn_feed_type(source.url_or_identifier)
    if feed_type not in HN_FEED_TYPES:
        raise ValueError(f"Invalid HN feed type: {source.url_or_identifier} (expected topstories, newstories, or beststories)")

    fetcher = provider or HackerNewsProvider()
    stories = fetcher.fetch_stories(feed_type)
    fetched_at = datetime.now(UTC)

    result = HackerNewsIngestionResult(
        source_id=source_id,
        stories_seen=len(stories),
        api_calls=1,
    )

    for story in stories:
        feed_item = _story_to_raw_item(
            story,
            source_id=source_id,
            fetched_at=fetched_at,
        )

        content_hash = feed_item.external_id
        if raw_items.upsert_item(
            source_id=source_id,
            item=feed_item,
            content_hash=content_hash,
            fetched_at=fetched_at,
        ):
            result.items_stored += 1

    sources.touch_last_crawled(source_id, fetched_at)
    return result


def run_due_hackernews_sources(
    *,
    sources: NewsSourceRepository,
    raw_items: NewsRawItemRepository,
    provider: HackerNewsProvider | None = None,
) -> list[HackerNewsIngestionResult]:
    """Fetch all due HN sources."""
    from datetime import timedelta

    now = datetime.now(UTC)
    results: list[HackerNewsIngestionResult] = []

    for source in sources.list_all():
        src = sources.get_by_id(source.id)
        if not src or not src.is_enabled or src.source_type != "hackernews":
            continue
        if src.last_crawled_at is not None:
            if src.last_crawled_at + timedelta(minutes=src.crawl_frequency_minutes) > now:
                continue
        try:
            results.append(
                run_hackernews_fetch(
                    src.id,
                    sources=sources,
                    raw_items=raw_items,
                    provider=provider,
                )
            )
        except ValueError as exc:
            result = HackerNewsIngestionResult(source_id=src.id, errors=[str(exc)])
            results.append(result)

    return results
