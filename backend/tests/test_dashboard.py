"""Tests for admin dashboard stats endpoint."""

from __future__ import annotations

import json
from time import time

from fastapi.testclient import TestClient

from backend.app.admin_boundary import ADMIN_IDENTITY_HEADER, ADMIN_SIGNATURE_HEADER, sign_admin_identity
from backend.app.main import create_app
from backend.app.settings import Settings


TEST_SECRET = Settings(environment="test").admin_boundary_secret.get_secret_value()


def _admin_headers() -> dict[str, str]:
    now = int(time())
    identity = {"user_id": "admin-1", "email": "admin@test.com", "role": "admin", "issued_at": now}
    payload = json.dumps(identity)
    return {
        ADMIN_IDENTITY_HEADER: payload,
        ADMIN_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET),
    }


def _test_app() -> TestClient:
    from backend.app.contact import InMemoryContactMessageRepository
    from backend.app.projects import InMemoryProjectRepository
    from backend.app.notifications import InMemoryNotificationRepository
    app = create_app(
        Settings(environment="test"),
        contact_repository=InMemoryContactMessageRepository(),
        project_repository=InMemoryProjectRepository(),
        notification_repository=InMemoryNotificationRepository(),
    )
    return TestClient(app)


def test_dashboard_stats_returns_counts() -> None:
    client = _test_app()
    resp = client.get("/admin/dashboard/stats", headers=_admin_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["blog_total"], int)
    assert isinstance(data["blog_published"], int)
    assert isinstance(data["blog_drafts"], int)
    assert isinstance(data["ideas_total"], int)
    assert isinstance(data["showcases_total"], int)
    assert isinstance(data["news_published"], int)
    assert isinstance(data["recent_activity"], list)


def test_dashboard_stats_requires_auth() -> None:
    client = _test_app()
    resp = client.get("/admin/dashboard/stats")
    assert resp.status_code == 401


def test_dashboard_stats_has_expected_keys() -> None:
    client = _test_app()
    resp = client.get("/admin/dashboard/stats", headers=_admin_headers())
    assert resp.status_code == 200
    data = resp.json()
    expected_keys = {
        "blog_drafts", "blog_published", "blog_total",
        "ideas_pending", "ideas_approved", "ideas_total",
        "showcases_drafts", "showcases_published", "showcases_total",
        "projects_drafts", "projects_published", "projects_total",
        "news_published", "comments_total", "recent_activity",
    }
    assert set(data.keys()) == expected_keys
