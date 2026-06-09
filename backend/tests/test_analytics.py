"""Tests for analytics aggregation (US-104)."""

from datetime import UTC, datetime, timedelta

import pytest

from backend.app.analytics_api import AnalyticsService
from backend.app.page_views import InMemoryPageViewRepository, PageView


def _seed_data(repo: InMemoryPageViewRepository) -> None:
    """Populate repo with test page views across multiple paths/dates/sessions."""
    now = datetime.now(UTC)
    repo._store = []

    # Today: 10 blog views, 5 about views, 3 project views
    for i in range(10):
        repo.create(PageView(id=f"t-{i}", path="/blog", session_id=f"s{i%3}", created_at=now))
    for i in range(5):
        repo.create(PageView(id=f"ta-{i}", path="/about", session_id=f"s{i%2}", created_at=now))
    for i in range(3):
        repo.create(PageView(id=f"tp-{i}", path="/projects", session_id="s1", created_at=now))

    # Yesterday: 5 blog views
    yesterday = now - timedelta(days=1)
    for i in range(5):
        repo.create(
            PageView(id=f"y-{i}", path="/blog", session_id=f"s{i%2}", created_at=yesterday)
        )

    # 10 days ago: 8 news views
    ten_days_ago = now - timedelta(days=10)
    for i in range(8):
        repo.create(
            PageView(id=f"10d-{i}", path="/ai-news", session_id="s99", created_at=ten_days_ago)
        )


class TestAnalyticsSummary:
    """AnalyticsService.get_summary()"""

    @pytest.fixture
    def service(self):
        repo = InMemoryPageViewRepository()
        _seed_data(repo)
        return AnalyticsService(repo), repo

    def test_total_views_all(self, service):
        svc, _ = service
        summary = svc.get_summary()
        assert summary.total_views_all == 31  # 10 + 5 + 3 + 5 + 8

    def test_total_views_today(self, service):
        svc, _ = service
        summary = svc.get_summary()
        assert summary.total_views_today == 18  # 10 + 5 + 3

    def test_total_views_7d(self, service):
        svc, _ = service
        summary = svc.get_summary()
        assert summary.total_views_7d == 23  # 18 today + 5 yesterday

    def test_total_views_30d(self, service):
        svc, _ = service
        summary = svc.get_summary()
        assert summary.total_views_30d == 31  # all within 30 days

    def test_unique_visitors_30d(self, service):
        svc, _ = service
        summary = svc.get_summary()
        # Unique sessions within 30d: s0, s1, s2 (today blog), s99 (10d ago ai-news) = 4
        assert summary.unique_visitors_30d == 4


class TestAnalyticsTopContent:
    """AnalyticsService.get_top_content()"""

    @pytest.fixture
    def service(self):
        repo = InMemoryPageViewRepository()
        _seed_data(repo)
        return AnalyticsService(repo)

    def test_returns_sorted(self, service):
        top = service.get_top_content(days=30, limit=10)
        assert len(top) >= 3
        assert top[0]["path"] == "/blog"
        assert top[0]["views"] == 15  # 10 today + 5 yesterday

    def test_limit(self, service):
        top = service.get_top_content(days=30, limit=2)
        assert len(top) == 2

    def test_empty_repo(self):
        svc = AnalyticsService(InMemoryPageViewRepository())
        top = svc.get_top_content(days=30)
        assert top == []


class TestAnalyticsTrends:
    """AnalyticsService.get_trends()"""

    @pytest.fixture
    def service(self):
        repo = InMemoryPageViewRepository()
        _seed_data(repo)
        return AnalyticsService(repo)

    def test_returns_all_days(self, service):
        trends = service.get_trends(days=7)
        assert len(trends) == 7

    def test_lists_zero_for_no_data(self, service):
        svc = AnalyticsService(InMemoryPageViewRepository())
        trends = svc.get_trends(days=3)
        assert len(trends) == 3
        assert all(t["views"] == 0 for t in trends)

    def test_has_data_in_today_slot(self, service):
        trends = service.get_trends(days=30)
        today_key = datetime.now(UTC).strftime("%Y-%m-%d")
        today_trend = next((t for t in trends if t["date"] == today_key), None)
        assert today_trend is not None
        assert today_trend["views"] == 18


class TestAnalyticsReferrers:
    """AnalyticsService.get_referrers()"""

    def test_direct_is_default(self):
        repo = InMemoryPageViewRepository()
        now = datetime.now(UTC)
        repo.create(PageView(id="r1", path="/blog", session_id="s1", created_at=now))
        repo.create(PageView(id="r2", path="/blog", session_id="s2", created_at=now))
        svc = AnalyticsService(repo)
        refs = svc.get_referrers(days=30)
        assert len(refs) == 1
        assert refs[0]["referrer"] == "(direct)"
        assert refs[0]["views"] == 2

    def test_with_referrer(self):
        repo = InMemoryPageViewRepository()
        now = datetime.now(UTC)
        repo.create(
            PageView(id="r1", path="/blog", session_id="s1", referrer="https://twitter.com", created_at=now)
        )
        repo.create(
            PageView(id="r2", path="/blog", session_id="s2", referrer="https://twitter.com", created_at=now)
        )
        repo.create(
            PageView(id="r3", path="/about", session_id="s3", referrer="https://google.com", created_at=now)
        )
        svc = AnalyticsService(repo)
        refs = svc.get_referrers(days=30)
        assert len(refs) == 2
        assert refs[0]["referrer"] == "https://twitter.com"
        assert refs[0]["views"] == 2
