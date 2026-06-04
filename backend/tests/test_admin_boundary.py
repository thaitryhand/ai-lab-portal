import json
from time import time

from fastapi.testclient import TestClient

from backend.app.admin_boundary import ADMIN_IDENTITY_HEADER, ADMIN_SIGNATURE_HEADER, sign_admin_identity
from backend.app.main import create_app
from backend.app.settings import Settings

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"


def _client() -> TestClient:
    return TestClient(create_app(Settings(environment="test", admin_boundary_secret=TEST_SECRET)))


def _identity_payload(**overrides: object) -> str:
    payload = {
        "user_id": "user_123",
        "email": "admin@example.com",
        "role": "admin",
        "issued_at": int(time()),
    }
    payload.update(overrides)
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def _headers(payload: str, secret: str = TEST_SECRET) -> dict[str, str]:
    return {
        ADMIN_IDENTITY_HEADER: payload,
        ADMIN_SIGNATURE_HEADER: sign_admin_identity(payload, secret),
    }


def test_admin_probe_rejects_missing_identity() -> None:
    response = _client().get("/admin/probe")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing admin identity"}


def test_admin_probe_rejects_tampered_identity_payload() -> None:
    payload = _identity_payload()
    tampered_payload = _identity_payload(email="attacker@example.com")

    response = _client().get("/admin/probe", headers={**_headers(payload), ADMIN_IDENTITY_HEADER: tampered_payload})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid identity signature"}


def test_admin_probe_rejects_non_admin_role() -> None:
    payload = _identity_payload(role="editor")

    response = _client().get("/admin/probe", headers=_headers(payload))

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid identity"}


def test_admin_probe_rejects_expired_identity() -> None:
    payload = _identity_payload(issued_at=int(time()) - 301)

    response = _client().get("/admin/probe", headers=_headers(payload))

    assert response.status_code == 401
    assert response.json() == {"detail": "Expired identity"}


def test_admin_probe_accepts_valid_admin_identity() -> None:
    payload = _identity_payload()

    response = _client().get("/admin/probe", headers=_headers(payload))

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "user_id": "user_123",
        "email": "admin@example.com",
        "role": "admin",
    }
