"""X/Twitter social source contract and fake provider fixtures (US-053).

This module deliberately contains no real provider calls. It defines the
normalized social-post boundary that future Apify/X provider adapters must emit
before an AI link filter or AI News ingestion step can use the data.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field, HttpUrl

SocialProviderName = Literal["apify_xquik", "apify_twitter_scraper", "fake"]
SocialSourceKind = Literal["handle", "search", "list", "tweet_url"]
SocialPostKind = Literal["original", "quote", "reply", "repost", "unknown"]


class SocialEngagementMetrics(BaseModel):
    like_count: int | None = Field(default=None, ge=0)
    repost_count: int | None = Field(default=None, ge=0)
    reply_count: int | None = Field(default=None, ge=0)
    quote_count: int | None = Field(default=None, ge=0)
    view_count: int | None = Field(default=None, ge=0)
    bookmark_count: int | None = Field(default=None, ge=0)


class SocialPostUrlEntity(BaseModel):
    url: HttpUrl
    expanded_url: HttpUrl | None = None
    display_url: str | None = None


class SocialPostSourceScope(BaseModel):
    provider: SocialProviderName
    provider_actor: str
    source_kind: SocialSourceKind
    source_value: str
    matched_query: str | None = None
    crawl_run_id: str | None = None


class NormalizedSocialPost(BaseModel):
    provider: SocialProviderName
    provider_actor: str
    post_id: str
    post_url: HttpUrl
    post_text: str = Field(min_length=1)
    post_kind: SocialPostKind = "unknown"
    created_at: datetime | None = None
    author_handle: str
    author_display_name: str | None = None
    author_verified: bool | None = None
    author_followers_count: int | None = Field(default=None, ge=0)
    lang: str | None = None
    engagement: SocialEngagementMetrics = Field(default_factory=SocialEngagementMetrics)
    urls: list[SocialPostUrlEntity] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    media_urls: list[HttpUrl] = Field(default_factory=list)
    quoted_post_id: str | None = None
    quoted_post_text: str | None = None
    quoted_author_handle: str | None = None
    reply_to_handle: str | None = None
    reply_to_post_id: str | None = None
    conversation_id: str | None = None
    source_scope: SocialPostSourceScope
    raw_payload: dict[str, Any]


class SocialProviderProtocol(Protocol):
    def fetch_posts(self, scope: SocialPostSourceScope) -> list[NormalizedSocialPost]: ...


def _http_url(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return None


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _extract_xquik_urls(row: dict[str, Any]) -> list[SocialPostUrlEntity]:
    entities = row.get("entities")
    urls: list[SocialPostUrlEntity] = []
    if isinstance(entities, dict):
        for item in entities.get("urls") or []:
            if not isinstance(item, dict):
                continue
            raw_url = _http_url(item.get("url"))
            expanded = _http_url(item.get("expanded_url") or item.get("expandedUrl"))
            candidate = expanded or raw_url
            if candidate is None:
                continue
            urls.append(
                SocialPostUrlEntity(
                    url=candidate,
                    expanded_url=expanded,
                    display_url=item.get("display_url") or item.get("displayUrl"),
                )
            )
    return urls


def _extract_media_urls(row: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for item in row.get("media") or []:
        if isinstance(item, dict):
            url = _http_url(item.get("url") or item.get("media_url_https"))
            if url:
                values.append(url)
    return values


def _post_kind_from_xquik(row: dict[str, Any]) -> SocialPostKind:
    if row.get("isQuoteStatus") is True or row.get("quoted_tweet"):
        return "quote"
    if row.get("isReply") is True:
        return "reply"
    if row.get("isRetweet") is True:
        return "repost"
    return "original"


def normalize_xquik_tweet(row: dict[str, Any], *, scope: SocialPostSourceScope) -> NormalizedSocialPost:
    """Normalize one Apify Xquik-like tweet row into the internal contract."""

    author = row.get("author") if isinstance(row.get("author"), dict) else {}
    post_id = str(row.get("id") or row.get("postId") or "")
    post_url = _http_url(row.get("url") or row.get("postUrl"))
    post_text = str(row.get("text") or row.get("postText") or "").strip()
    author_handle = str(author.get("username") or row.get("authorHandle") or "").lstrip("@")

    if not post_id:
        raise ValueError("X/Twitter post id is required")
    if post_url is None:
        raise ValueError("X/Twitter post URL is required")
    if not post_text:
        raise ValueError("X/Twitter post text is required")
    if not author_handle:
        raise ValueError("X/Twitter author handle is required")

    quoted = row.get("quoted_tweet") if isinstance(row.get("quoted_tweet"), dict) else {}

    return NormalizedSocialPost(
        provider=scope.provider,
        provider_actor=scope.provider_actor,
        post_id=post_id,
        post_url=post_url,
        post_text=post_text,
        post_kind=_post_kind_from_xquik(row),
        created_at=row.get("createdAt") or row.get("postDateTime"),
        author_handle=author_handle,
        author_display_name=author.get("name") or row.get("authorDisplayName"),
        author_verified=author.get("verified") if "verified" in author else None,
        author_followers_count=_int_or_none(author.get("followers")),
        lang=row.get("lang"),
        engagement=SocialEngagementMetrics(
            like_count=_int_or_none(row.get("likeCount") or row.get("nbLikes")),
            repost_count=_int_or_none(row.get("retweetCount") or row.get("nbReposts")),
            reply_count=_int_or_none(row.get("replyCount") or row.get("nbReplies")),
            quote_count=_int_or_none(row.get("quoteCount")),
            view_count=_int_or_none(row.get("viewCount") or row.get("nbViews")),
            bookmark_count=_int_or_none(row.get("bookmarkCount") or row.get("nbBookmarks")),
        ),
        urls=_extract_xquik_urls(row),
        hashtags=[item.get("text", "") for item in (row.get("entities") or {}).get("hashtags", []) if isinstance(item, dict)],
        media_urls=_extract_media_urls(row),
        quoted_post_id=row.get("quotedPostId") or quoted.get("id"),
        quoted_post_text=row.get("quotedPostText") or quoted.get("text"),
        quoted_author_handle=row.get("quotedAuthorHandle") or (quoted.get("author") or {}).get("username") if isinstance(quoted.get("author"), dict) else row.get("quotedAuthorHandle"),
        reply_to_handle=row.get("replyToHandle"),
        reply_to_post_id=row.get("replyToPostId"),
        conversation_id=row.get("conversationId"),
        source_scope=scope,
        raw_payload=row,
    )


class FakeXTwitterProvider:
    """Deterministic fake provider returning normalized Apify-like fixture rows."""

    def __init__(self, rows: Iterable[dict[str, Any]] | None = None) -> None:
        self._rows = list(rows) if rows is not None else list(FAKE_XQUIK_ROWS)

    def fetch_posts(self, scope: SocialPostSourceScope) -> list[NormalizedSocialPost]:
        return [normalize_xquik_tweet(row, scope=scope) for row in self._rows]


FAKE_XQUIK_ROWS: tuple[dict[str, Any], ...] = (
    {
        "id": "1846987139428634858",
        "text": "OpenAI shipped a new agent workflow with eval notes https://openai.com/research/agents",
        "createdAt": "2026-06-04T10:00:00Z",
        "likeCount": 420,
        "retweetCount": 88,
        "replyCount": 31,
        "quoteCount": 12,
        "viewCount": 54000,
        "bookmarkCount": 100,
        "lang": "en",
        "url": "https://x.com/OpenAI/status/1846987139428634858",
        "author": {
            "id": "4398626122",
            "username": "OpenAI",
            "name": "OpenAI",
            "followers": 5000000,
            "verified": True,
        },
        "entities": {
            "hashtags": [{"text": "AI"}],
            "urls": [
                {
                    "url": "https://t.co/example",
                    "expanded_url": "https://openai.com/research/agents",
                    "display_url": "openai.com/research/agents",
                }
            ],
        },
        "isQuoteStatus": False,
        "isReply": False,
        "conversationId": "1846987139428634858",
    },
    {
        "id": "1846987139428634859",
        "text": "This benchmark thread compares long-context model behavior.",
        "createdAt": "2026-06-04T11:00:00Z",
        "likeCount": 150,
        "retweetCount": 29,
        "replyCount": 9,
        "quoteCount": 4,
        "viewCount": 22000,
        "bookmarkCount": 44,
        "lang": "en",
        "url": "https://x.com/researcher/status/1846987139428634859",
        "author": {"username": "researcher", "name": "AI Researcher", "followers": 80000, "verified": False},
        "entities": {"hashtags": [{"text": "LLM"}], "urls": []},
        "quoted_tweet": {
            "id": "1846987139428634000",
            "text": "New long-context eval results are out.",
            "author": {"username": "evals_lab"},
        },
        "isQuoteStatus": True,
        "conversationId": "1846987139428634000",
    },
)
