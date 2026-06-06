"""Seed a published blog post via the AI Blog Agent pipeline (deterministic fake LLM).

Requires backend on :18000 with:
  AI_LAB_LLM_E2E_FAKE=true
  AI_LAB_DATABASE_URL=postgresql+psycopg://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal

Celery runs inline when llm_e2e_fake is enabled (task_always_eager).

Usage:
  python scripts/seed_blog_agent_pipeline.py
  python scripts/seed_blog_agent_pipeline.py --skip-publish
  python scripts/seed_blog_agent_pipeline.py --idea-id <existing>
"""

from __future__ import annotations

import argparse
import sys
from urllib.error import URLError
from urllib.request import urlopen

sys.path.insert(0, "D:/Personal/ai-lab-portal")

from scripts.blog_agent_common import (  # noqa: E402
    BACKEND_URL,
    SEED_PROJECT_PAYLOAD,
    generate_idea,
    load_idea,
    publish_idea,
    run_semi_auto_pipeline,
    seed_project,
    waive_pending_claims,
)

FIXED_PROJECT_ID = "project_seed_blog_agent"
FIXED_PROJECT_SLUG = "ai-lab-portal-blog-agent"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed editorial content via AI Blog Agent (fake LLM, no OpenAI key)"
    )
    parser.add_argument("--skip-seed-project", action="store_true")
    parser.add_argument("--skip-publish", action="store_true")
    parser.add_argument("--no-waive-claims", action="store_true")
    parser.add_argument("--idea-id", help="Resume an existing idea (skip generate)")
    args = parser.parse_args()

    try:
        urlopen(f"{BACKEND_URL}/health", timeout=5)
    except URLError as exc:
        raise SystemExit(
            f"Backend not reachable at {BACKEND_URL}.\n"
            "Start with: AI_LAB_LLM_E2E_FAKE=true python -m uvicorn backend.app.main:app --port 18000\n"
            f"{exc}"
        ) from exc

    if not args.skip_seed_project:
        seed_project(project_id=FIXED_PROJECT_ID, slug=FIXED_PROJECT_SLUG)

    print("\n1. Generate idea (fake LLM)...", flush=True)
    if args.idea_id:
        idea_id = args.idea_id
        idea = load_idea(idea_id)
        print(f"   Resuming idea: {idea.get('title', idea_id)} ({idea_id})")
    else:
        idea_id, idea = generate_idea(SEED_PROJECT_PAYLOAD)
        print(f"   Idea: {idea.get('title', idea_id)} ({idea_id})")

    idea = run_semi_auto_pipeline(idea_id, idea)

    if not args.no_waive_claims:
        print("7. Waive pending claims (if any)...", flush=True)
        waive_pending_claims(idea_id)

    if args.skip_publish:
        print("\n=== SEED PIPELINE COMPLETE (not published) ===")
        print(f"Admin: http://127.0.0.1:13000/admin/blog-ideas/{idea_id}")
        return

    print("8. Publish to blog...", flush=True)
    publish = publish_idea(idea_id)

    slug = publish.get("slug")
    post_id = publish.get("blog_post_id")
    print("\n=== SEED COMPLETE ===")
    print(f"Admin:  http://127.0.0.1:13000/admin/blog-ideas/{idea_id}")
    print(f"Public: http://127.0.0.1:13000/blog/{slug}")
    print(f"Post id: {post_id}")


if __name__ == "__main__":
    main()
