"""Tests for event tracking and CSV export (US-106)."""

import csv
import io
from datetime import UTC, datetime, timedelta

import pytest

from backend.app.events import (
    Event,
    InMemoryEventRepository,
    TrackEventRequest,
    _export_events_csv,
    _export_page_views_csv,
)
from backend.app.page_views import InMemoryPageViewRepository, PageView


class TestEventRepository:
    """EventRepository CRUD operations."""

    @pytest.fixture
    def repo(self):
        return InMemoryEventRepository()

    def make_event(self, event_type: str = "click", path: str = "/blog", session_id: str = "s1", **kw):
        return Event(
            id=f"evt-{event_type}-{session_id}",
            path=path,
            event_type=event_type,
            session_id=session_id,
            created_at=kw.pop("created_at", datetime.now(UTC)),
            **kw,
        )

    def test_create_and_count(self, repo):
        repo.create(self.make_event())
        assert repo.count_total() == 1

    def test_count_by_type(self, repo):
        repo.create(self.make_event("click"))
        repo.create(self.make_event("click"))
        repo.create(self.make_event("share"))
        assert repo.count_by_type("click") == 2
        assert repo.count_by_type("share") == 1
        assert repo.count_by_type("comment") == 0

    def test_count_since(self, repo):
        old = datetime.now(UTC) - timedelta(hours=5)
        recent = datetime.now(UTC)
        repo.create(self.make_event("click", created_at=old))
        repo.create(self.make_event("share", created_at=recent))
        since = datetime.now(UTC) - timedelta(hours=1)
        assert repo.count_total(since=since) == 1

    def test_get_all_since(self, repo):
        old = datetime.now(UTC) - timedelta(hours=5)
        recent = datetime.now(UTC)
        repo.create(self.make_event("click", created_at=old))
        repo.create(self.make_event("share", created_at=recent))
        since = datetime.now(UTC) - timedelta(hours=1)
        events = repo.get_all_since(since)
        assert len(events) == 1
        assert events[0].event_type == "share"

    def test_empty_repo(self, repo):
        assert repo.count_total() == 0
        assert repo.count_by_type("click") == 0


class TestTrackEventRequest:
    """Pydantic model validation."""

    def test_valid_request(self):
        req = TrackEventRequest(path="/blog", event_type="share", session_id="s1")
        assert req.path == "/blog"
        assert req.event_type == "share"

    def test_invalid_event_type(self):
        with pytest.raises(ValueError, match="String should match pattern"):
            TrackEventRequest(path="/blog", event_type="invalid", session_id="s1")

    def test_with_metadata(self):
        req = TrackEventRequest(
            path="/blog", event_type="click", session_id="s1",
            event_metadata='{"button": "share-twitter"}',
        )
        assert req.event_metadata == '{"button": "share-twitter"}'


class TestCSVExport:
    """CSV export functionality."""

    @pytest.fixture
    def page_view_repo(self):
        repo = InMemoryPageViewRepository()
        now = datetime.now(UTC)
        for i in range(3):
            repo.create(PageView(
                id=f"pv-{i}", path=f"/page-{i}", session_id="s1", created_at=now,
            ))
        return repo

    @pytest.fixture
    def event_repo(self):
        repo = InMemoryEventRepository()
        now = datetime.now(UTC)
        for i in range(2):
            repo.create(Event(
                id=f"evt-{i}", path="/blog", event_type="click",
                session_id="s1", created_at=now,
            ))
        return repo

    def test_export_page_views_csv(self, page_view_repo):
        since = datetime.now(UTC) - timedelta(days=30)
        csv_str = _export_page_views_csv(page_view_repo, since)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) == 3
        assert rows[0]["path"] == "/page-0"

    def test_export_events_csv(self, event_repo):
        since = datetime.now(UTC) - timedelta(days=30)
        csv_str = _export_events_csv(event_repo, since)
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["event_type"] == "click"

    def test_export_events_csv_filtered(self, event_repo):
        since = datetime.now(UTC) - timedelta(days=30)
        csv_str = _export_events_csv(event_repo, since, event_type="share")
        reader = csv.DictReader(io.StringIO(csv_str))
        rows = list(reader)
        assert len(rows) == 0  # No share events

    def test_export_empty(self):
        csv_str = _export_page_views_csv(InMemoryPageViewRepository(), datetime.now(UTC))
        reader = csv.DictReader(io.StringIO(csv_str))
        assert len(list(reader)) == 0

    def test_csv_headers(self, event_repo):
        since = datetime.now(UTC) - timedelta(days=30)
        csv_str = _export_events_csv(event_repo, since)
        reader = csv.DictReader(io.StringIO(csv_str))
        assert "id" in reader.fieldnames
        assert "event_type" in reader.fieldnames
        assert "path" in reader.fieldnames
