"""Shared helpers for AI Blog Agent pipeline scripts (dogfood + seed)."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from backend.app.admin_boundary import sign_admin_identity

BACKEND_URL = "http://127.0.0.1:18000"
SECRET = "ai-lab-dev-boundary-2026-secret!"
DATABASE_URL = "postgresql://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal"
POLL_INTERVAL_SEC = 2
JOB_TIMEOUT_SEC = 300

SEED_PROJECT_PAYLOAD = {
    "project_name": "AI Lab Portal",
    "project_summary": (
        "A web portal and harness for agent-ready software repos: blog, projects, "
        "showcases, and a semi-automated AI blog agent pipeline."
    ),
    "ai_capabilities": (
        "LLM-powered idea generation, outline and draft writing, technical review, "
        "SEO marketing metadata, and claim extraction with human approval gates."
    ),
    "technical_highlights": (
        "## Stack\n"
        "FastAPI backend, Next.js admin UI, Celery + Redis async jobs, Postgres persistence.\n\n"
        "## Blog agent\n"
        "Semi-auto orchestrator: admin approves each gate before the next LLM stage runs.\n"
        "Publish bridge creates a public blog post when draft, review, marketing, and claims are ready."
    ),
    "business_value": (
        "Ships publishable technical blog content from real project context with editorial control."
    ),
}


def admin_headers(user_id: str = "pipeline_script") -> dict[str, str]:
    payload = json.dumps(
        {
            "user_id": user_id,
            "email": "admin@example.com",
            "role": "admin",
            "issued_at": int(time.time()),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return {
        "x-ai-lab-admin-identity": payload,
        "x-ai-lab-admin-signature": sign_admin_identity(payload, SECRET),
        "Content-Type": "application/json",
    }


def api_call(method: str, path: str, body: dict | None = None) -> tuple[int, Any]:
    url = f"{BACKEND_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = Request(url, data=data, method=method, headers=admin_headers())
    try:
        with urlopen(req, timeout=120) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else None
    except HTTPError as exc:
        raw = exc.read().decode()
        try:
            detail = json.loads(raw)
        except json.JSONDecodeError:
            detail = raw
        return exc.code, detail


def seed_project(
    *,
    project_id: str | None = None,
    slug: str | None = None,
    title: str | None = None,
    description: str | None = None,
    content_markdown: str | None = None,
) -> str:
    import psycopg

    resolved_id = project_id or f"project_seed_{uuid.uuid4().hex[:8]}"
    resolved_slug = slug or f"ai-lab-portal-seed-{uuid.uuid4().hex[:6]}"
    conn = psycopg.connect(DATABASE_URL)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into projects (
                  id, slug, title, description, content_markdown,
                  status, published_at, created_at, updated_at
                )
                values (%s, %s, %s, %s, %s, 'published', now(), now(), now())
                on conflict (id) do nothing
                """,
                (
                    resolved_id,
                    resolved_slug,
                    title or SEED_PROJECT_PAYLOAD["project_name"],
                    description or SEED_PROJECT_PAYLOAD["project_summary"],
                    content_markdown or SEED_PROJECT_PAYLOAD["technical_highlights"],
                ),
            )
        conn.commit()
    finally:
        conn.close()
    print(f"Seeded published project {resolved_id} ({resolved_slug})")
    return resolved_id


def latest_idea_id() -> str:
    status, ideas = api_call("GET", "/admin/blog-ideas")
    if status >= 300 or not ideas:
        raise RuntimeError(f"Could not list ideas ({status})")
    return max(ideas, key=lambda row: row.get("created_at", ""))["id"]


def wait_for_job(task_id: str, label: str) -> None:
    deadline = time.time() + JOB_TIMEOUT_SEC
    while time.time() < deadline:
        status, body = api_call("GET", f"/admin/blog-ideas/generation-jobs/{task_id}")
        if status != 200:
            raise RuntimeError(f"{label}: job status failed ({status}) {body}")
        job_status = body.get("status")
        if job_status == "completed":
            print(f"   {label}: completed")
            return
        if job_status == "failed":
            raise RuntimeError(f"{label}: job failed — {body.get('error_message')}")
        time.sleep(POLL_INTERVAL_SEC)
    raise TimeoutError(f"{label}: timed out after {JOB_TIMEOUT_SEC}s")


def dispatch_and_wait(method: str, path: str, body: dict | None, label: str) -> Any:
    status, result = api_call(method, path, body)
    if status == 202:
        task_id = (result.get("detail") or result).get("task_id")
        if not task_id:
            raise RuntimeError(f"{label}: 202 without task_id — {result}")
        print(f"   {label}: queued ({task_id})")
        wait_for_job(task_id, label)
        return None
    if 200 <= status < 300:
        print(f"   {label}: done inline")
        return result
    raise RuntimeError(f"{label}: failed ({status}) {result}")


def load_idea(idea_id: str) -> dict[str, Any]:
    status, idea = api_call("GET", f"/admin/blog-ideas/{idea_id}")
    if status >= 300:
        raise RuntimeError(f"Could not load idea {idea_id} ({status})")
    return idea


def approve_and_run(idea_id: str, patch: dict[str, str], post_path: str, label: str) -> None:
    status, result = api_call("PATCH", f"/admin/blog-ideas/{idea_id}", patch)
    if status >= 300:
        raise RuntimeError(f"Approve {label}: PATCH failed ({status}) {result}")
    dispatch_and_wait("POST", post_path, {}, label)


def maybe_approve_and_run(
    idea: dict[str, Any],
    idea_id: str,
    *,
    gate_field: str,
    gate_value: str,
    post_path: str,
    label: str,
    skip_if: bool,
) -> dict[str, Any]:
    if skip_if:
        print(f"   {label}: skipped (already done)")
        return idea
    approve_and_run(idea_id, {gate_field: gate_value}, post_path, label)
    return load_idea(idea_id)


def waive_pending_claims(idea_id: str) -> None:
    status, claims = api_call("GET", f"/admin/blog-ideas/{idea_id}/claims")
    if status >= 300:
        raise RuntimeError(f"List claims failed ({status}) {claims}")
    pending = [c for c in claims if c.get("status") == "pending"]
    if not pending:
        print(f"   Claims: none pending ({len(claims)} total)")
        return
    print(f"   Waiving {len(pending)} pending claim(s)...")
    for claim in pending:
        status, result = api_call(
            "PATCH",
            f"/admin/blog-ideas/claims/{claim['id']}",
            {"status": "waived"},
        )
        if status >= 300:
            raise RuntimeError(f"Waive claim failed ({status}) {result}")


def generate_idea(payload: dict[str, str] | None = None) -> tuple[str, dict[str, Any]]:
    body = payload or SEED_PROJECT_PAYLOAD
    status, result = api_call("POST", "/admin/blog-ideas/generate", body)
    if status == 202:
        task_id = (result.get("detail") or result).get("task_id")
        wait_for_job(task_id, "Idea generation")
        idea_id = latest_idea_id()
        idea = load_idea(idea_id)
        return idea_id, idea
    if 200 <= status < 300:
        return result["id"], result
    raise RuntimeError(f"Generate failed ({status}) {result}")


def run_semi_auto_pipeline(idea_id: str, idea: dict[str, Any]) -> dict[str, Any]:
    print("2. Approve idea -> outline...", flush=True)
    idea = maybe_approve_and_run(
        idea,
        idea_id,
        gate_field="status",
        gate_value="approved",
        post_path=f"/admin/blog-ideas/{idea_id}/generate-outline",
        label="Outline",
        skip_if=idea.get("status") == "approved" and bool(idea.get("outline_sections")),
    )

    print("3. Approve outline -> draft...", flush=True)
    idea = maybe_approve_and_run(
        idea,
        idea_id,
        gate_field="outline_status",
        gate_value="approved",
        post_path=f"/admin/blog-ideas/{idea_id}/generate-draft",
        label="Draft",
        skip_if=idea.get("outline_status") == "approved" and bool(idea.get("draft_markdown")),
    )

    print("4. Approve draft -> technical review...", flush=True)
    idea = maybe_approve_and_run(
        idea,
        idea_id,
        gate_field="draft_status",
        gate_value="approved",
        post_path=f"/admin/blog-ideas/{idea_id}/review-technical",
        label="Technical review",
        skip_if=idea.get("draft_status") == "approved" and bool(idea.get("technical_review")),
    )

    print("5. Accept review -> marketing...", flush=True)
    if idea.get("marketing_metadata"):
        print("   Marketing: skipped (already done)")
    else:
        if idea.get("technical_review_status") != "approved":
            status, _ = api_call(
                "PATCH",
                f"/admin/blog-ideas/{idea_id}",
                {"technical_review_status": "approved"},
            )
            if status >= 300:
                raise RuntimeError(f"Accept review failed ({status})")
        dispatch_and_wait(
            "POST",
            f"/admin/blog-ideas/{idea_id}/generate-marketing",
            {},
            "Marketing",
        )
        idea = load_idea(idea_id)

    print("6. Approve marketing -> extract claims...", flush=True)
    if idea.get("marketing_status") != "approved":
        status, _ = api_call(
            "PATCH",
            f"/admin/blog-ideas/{idea_id}",
            {"marketing_status": "approved"},
        )
        if status >= 300:
            raise RuntimeError(f"Approve marketing failed ({status})")
    status, claims = api_call("GET", f"/admin/blog-ideas/{idea_id}/claims")
    if status >= 300:
        raise RuntimeError(f"List claims failed ({status})")
    if not claims:
        status, claims = api_call("POST", f"/admin/blog-ideas/{idea_id}/extract-claims", {})
        if status >= 300:
            raise RuntimeError(f"Extract claims failed ({status}) {claims}")
    print(f"   Claims extracted: {len(claims)}")
    return idea


def publish_idea(idea_id: str) -> dict[str, Any]:
    status, publish = api_call("POST", f"/admin/blog-ideas/{idea_id}/publish-to-blog", {})
    if status >= 300:
        raise RuntimeError(f"Publish failed ({status}) {publish}")
    return publish
