"""Tests for X/Twitter source contract and fake provider fixtures (US-053)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.app.social_x import (
    FAKE_XQUIK_ROWS,
    FakeXTwitterProvider,
    NormalizedSocialPost,
    SocialPostSourceScope,
    normalize_xquik_tweet,
)


def _scope() -> SocialPostSourceScope:
    return SocialPostSourceScope(
        provider="apify_xquik",
        provider_actor="xquik/x-tweet-scraper",
        source_kind="handle",
        source_value="OpenAI",
        matched_query="from:OpenAI AI",
        crawl_run_id="run_123",
    )


def test_normalize_xquik_tweet_maps_required_fields() -> None:
    post = normalize_xquik_tweet(FAKE_XQUIK_ROWS[0], scope=_scope())

    assert isinstance(post, NormalizedSocialPost)
    assert post.provider == "apify_xquik"
    assert post.provider_actor == "xquik/x-tweet-scraper"
    assert post.post_id == "1846987139428634858"
    assert str(post.post_url) == "https://x.com/OpenAI/status/1846987139428634858"
    assert post.author_handle == "OpenAI"
    assert post.author_followers_count == 5_000_000
    assert post.engagement.like_count == 420
    assert post.engagement.repost_count == 88
    assert post.engagement.view_count == 54_000
    assert post.hashtags == ["AI"]
    assert str(post.urls[0].url) == "https://openai.com/research/agents"
    assert post.source_scope.source_value == "OpenAI"
    assert post.raw_payload["id"] == "1846987139428634858"


def test_normalize_xquik_tweet_maps_quote_context() -> None:
    post = normalize_xquik_tweet(FAKE_XQUIK_ROWS[1], scope=_scope())

    assert post.post_kind == "quote"
    assert post.quoted_post_id == "1846987139428634000"
    assert post.quoted_post_text == "New long-context eval results are out."
    assert post.quoted_author_handle == "evals_lab"
    assert post.conversation_id == "1846987139428634000"


def test_fake_provider_returns_normalized_posts_without_real_provider_calls() -> None:
    provider = FakeXTwitterProvider()
    posts = provider.fetch_posts(_scope())

    assert len(posts) == 2
    assert all(isinstance(post, NormalizedSocialPost) for post in posts)
    assert {post.post_kind for post in posts} == {"original", "quote"}


@pytest.mark.parametrize(
    "missing_field",
    ["id", "url", "text"],
)
def test_normalize_xquik_tweet_rejects_missing_required_provider_fields(missing_field: str) -> None:
    row = dict(FAKE_XQUIK_ROWS[0])
    row.pop(missing_field)

    with pytest.raises(ValueError):
        normalize_xquik_tweet(row, scope=_scope())


def test_normalized_social_post_rejects_non_http_urls() -> None:
    with pytest.raises(ValidationError):
        NormalizedSocialPost(
            provider="fake",
            provider_actor="fake",
            post_id="post_1",
            post_url="ftp://example.com/post",
            post_text="AI news",
            author_handle="author",
            source_scope=SocialPostSourceScope(
                provider="fake",
                provider_actor="fake",
                source_kind="search",
                source_value="AI",
            ),
            raw_payload={},
        )
