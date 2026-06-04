"""Tests for projects CRUD (US-066)."""

from __future__ import annotations

import json
from time import time

from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.admin_boundary import ADMIN_IDENTITY_HEADER, ADMIN_SIGNATURE_HEADER, sign_admin_identity
from backend.app.main import create_app
from backend.app.projects import (
    AdminProjectDetail,
    AdminProjectSummary,
    InMemoryProjectRepository,
    ProjectCreate,
    ProjectDetail,
    ProjectSummary,
    ProjectUpdate,
)
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


def _make_body(
    slug: str = "test-project",
    title: str = "Test Project",
    description: str = "A test project description.",
    content_markdown: str = "# Test\n\nSome markdown content.",
) -> dict[str, str]:
    return {
        "slug": slug,
        "title": title,
        "description": description,
        "content_markdown": content_markdown,
    }


def _make_app():
    """Create app with in-memory project repo for testing."""
    repo = InMemoryProjectRepository()
    app = create_app(project_repository=repo)
    return TestClient(app), repo


# --- Unit: model validation ---

def test_project_create_validates_required_fields() -> None:
    """Empty title should raise validation error."""
    try:
        ProjectCreate(**{"slug": "x", "title": "", "description": "x", "content_markdown": "x"})
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_project_create_validates_slug_pattern() -> None:
    """Slug must match pattern."""
    try:
        ProjectCreate(**{"slug": "UPPERCASE", "title": "x", "description": "x", "content_markdown": "x"})
        assert False, "Expected ValidationError"
    except ValidationError:
        pass


def test_project_create_slug_pattern_valid() -> None:
    """Lowercase dashed slug is valid."""
    model = ProjectCreate(**{"slug": "my-valid-slug", "title": "x", "description": "x", "content_markdown": "x"})
    assert model.slug == "my-valid-slug"


# --- Unit: InMemoryProjectRepository ---

def test_inmemory_create_and_list_all() -> None:
    repo = InMemoryProjectRepository()
    body = _make_body()
    repo.create(ProjectCreate(**body))
    all_items = repo.list_all()
    assert len(all_items) == 1
    assert isinstance(all_items[0], AdminProjectSummary)
    assert all_items[0].title == "Test Project"
    assert all_items[0].status == "draft"


def test_inmemory_create_sets_draft() -> None:
    repo = InMemoryProjectRepository()
    project = repo.create(ProjectCreate(**_make_body()))
    assert project.status == "draft"
    assert project.published_at is None
    assert project.created_at is not None
    assert project.updated_at is not None


def test_inmemory_get_by_id() -> None:
    repo = InMemoryProjectRepository()
    project = repo.create(ProjectCreate(**_make_body()))
    detail = repo.get_by_id(project.id)
    assert detail is not None
    assert isinstance(detail, AdminProjectDetail)
    assert detail.title == "Test Project"
    assert detail.description == "A test project description."


def test_inmemory_get_by_id_not_found() -> None:
    repo = InMemoryProjectRepository()
    assert repo.get_by_id("nonexistent") is None


def test_inmemory_update() -> None:
    repo = InMemoryProjectRepository()
    project = repo.create(ProjectCreate(**_make_body()))
    updated = repo.update(project.id, ProjectUpdate(title="Updated Title"))
    assert updated is not None
    assert updated.title == "Updated Title"


def test_inmemory_update_not_found() -> None:
    repo = InMemoryProjectRepository()
    assert repo.update("nonexistent", ProjectUpdate(title="x")) is None


def test_inmemory_publish() -> None:
    repo = InMemoryProjectRepository()
    project = repo.create(ProjectCreate(**_make_body()))
    published = repo.publish(project.id)
    assert published is not None
    assert published.status == "published"
    assert published.published_at is not None


def test_inmemory_publish_not_found() -> None:
    repo = InMemoryProjectRepository()
    assert repo.publish("nonexistent") is None


def test_inmemory_unpublish() -> None:
    repo = InMemoryProjectRepository()
    project = repo.create(ProjectCreate(**_make_body()))
    repo.publish(project.id)
    unpublished = repo.unpublish(project.id)
    assert unpublished is not None
    assert unpublished.status == "draft"
    assert unpublished.published_at is None


def test_inmemory_unpublish_not_found() -> None:
    repo = InMemoryProjectRepository()
    assert repo.unpublish("nonexistent") is None


def test_inmemory_list_published_only() -> None:
    repo = InMemoryProjectRepository()
    repo.create(ProjectCreate(**_make_body(slug="draft-1", title="Draft 1")))
    repo.create(ProjectCreate(**_make_body(slug="pub-1", title="Published 1")))
    pub2 = repo.create(ProjectCreate(**_make_body(slug="pub-2", title="Published 2")))
    repo.publish(pub2.id)
    published = repo.list_published()
    assert len(published) == 1
    assert isinstance(published[0], ProjectSummary)
    assert published[0].title == "Published 2"


def test_inmemory_get_published_by_slug() -> None:
    repo = InMemoryProjectRepository()
    project = repo.create(ProjectCreate(**_make_body()))
    assert repo.get_published_by_slug("test-project") is None
    repo.publish(project.id)
    detail = repo.get_published_by_slug("test-project")
    assert detail is not None
    assert isinstance(detail, ProjectDetail)
    assert detail.title == "Test Project"


def test_inmemory_slug_exists() -> None:
    repo = InMemoryProjectRepository()
    repo.create(ProjectCreate(**_make_body()))
    assert repo.slug_exists("test-project") is True
    assert repo.slug_exists("other-slug") is False


def test_inmemory_slug_exists_exclude_self() -> None:
    repo = InMemoryProjectRepository()
    project = repo.create(ProjectCreate(**_make_body()))
    assert repo.slug_exists("test-project", exclude_id=project.id) is False


def test_inmemory_record_audit() -> None:
    repo = InMemoryProjectRepository()
    event = repo.record_audit("user-1", "admin@test.com", "project.published", "project-1")
    assert event.action == "project.published"
    assert event.entity_id == "project-1"
    assert event.entity_type == "project"


# --- API: admin routes ---

def test_admin_create_project() -> None:
    client, _ = _make_app()
    body = _make_body()
    resp = client.post("/admin/projects", json=body, headers=_admin_headers())
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["title"] == "Test Project"
    assert data["status"] == "draft"
    assert data["slug"] == "test-project"


def test_admin_create_project_duplicate_slug() -> None:
    client, _ = _make_app()
    body = _make_body()
    client.post("/admin/projects", json=body, headers=_admin_headers())
    resp = client.post("/admin/projects", json=body, headers=_admin_headers())
    assert resp.status_code == 409


def test_admin_list_projects() -> None:
    client, _ = _make_app()
    client.post("/admin/projects", json=_make_body(slug="p1", title="P1"), headers=_admin_headers())
    client.post("/admin/projects", json=_make_body(slug="p2", title="P2"), headers=_admin_headers())
    resp = client.get("/admin/projects", headers=_admin_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_admin_get_project() -> None:
    client, _ = _make_app()
    create_resp = client.post("/admin/projects", json=_make_body(), headers=_admin_headers())
    project_id = create_resp.json()["id"]
    resp = client.get(f"/admin/projects/{project_id}", headers=_admin_headers())
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test Project"


def test_admin_get_project_not_found() -> None:
    client, _ = _make_app()
    resp = client.get("/admin/projects/nonexistent", headers=_admin_headers())
    assert resp.status_code == 404


def test_admin_update_project() -> None:
    client, _ = _make_app()
    create_resp = client.post("/admin/projects", json=_make_body(), headers=_admin_headers())
    project_id = create_resp.json()["id"]
    resp = client.patch(f"/admin/projects/{project_id}", json={"title": "Updated"}, headers=_admin_headers())
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


def test_admin_update_project_not_found() -> None:
    client, _ = _make_app()
    resp = client.patch("/admin/projects/nonexistent", json={"title": "x"}, headers=_admin_headers())
    assert resp.status_code == 404


def test_admin_publish_project() -> None:
    client, _ = _make_app()
    create_resp = client.post("/admin/projects", json=_make_body(), headers=_admin_headers())
    project_id = create_resp.json()["id"]
    resp = client.post(f"/admin/projects/{project_id}/publish", headers=_admin_headers())
    assert resp.status_code == 200
    assert resp.json()["status"] == "published"
    assert resp.json()["published_at"] is not None


def test_admin_unpublish_project() -> None:
    client, _ = _make_app()
    create_resp = client.post("/admin/projects", json=_make_body(), headers=_admin_headers())
    project_id = create_resp.json()["id"]
    client.post(f"/admin/projects/{project_id}/publish", headers=_admin_headers())
    resp = client.post(f"/admin/projects/{project_id}/unpublish", headers=_admin_headers())
    assert resp.status_code == 200
    assert resp.json()["status"] == "draft"


def test_admin_project_requires_auth() -> None:
    client, _ = _make_app()
    resp = client.get("/admin/projects")
    assert resp.status_code == 401


# --- API: public routes ---

def test_public_list_projects() -> None:
    client, repo = _make_app()
    project = repo.create(ProjectCreate(**_make_body()))
    repo.publish(project.id)
    resp = client.get("/public/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Project"
    # Public response should not include content_markdown
    assert "content_markdown" not in data[0]


def test_public_list_projects_empty_when_no_published() -> None:
    client, _ = _make_app()
    resp = client.get("/public/projects")
    assert resp.status_code == 200
    assert resp.json() == []


def test_public_get_project_by_slug() -> None:
    client, repo = _make_app()
    project = repo.create(ProjectCreate(**_make_body()))
    repo.publish(project.id)
    resp = client.get("/public/projects/test-project")
    assert resp.status_code == 200
    assert resp.json()["title"] == "Test Project"
    assert "content_markdown" in resp.json()


def test_public_get_project_not_found() -> None:
    client, _ = _make_app()
    resp = client.get("/public/projects/nonexistent")
    assert resp.status_code == 404


def test_public_get_project_not_published() -> None:
    client, repo = _make_app()
    repo.create(ProjectCreate(**_make_body()))
    resp = client.get("/public/projects/test-project")
    assert resp.status_code == 404
