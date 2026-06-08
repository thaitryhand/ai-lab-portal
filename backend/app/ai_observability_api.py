"""Admin API routes for the AI observability dashboard.

Exposes:
- ``GET /admin/ai-observability/stats`` — aggregated statistics (latency, tokens, stages)
- ``GET /admin/ai-observability/runs`` — recent AI run history

Mounted by ``create_app()`` under the default FastAPI app.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, Header, Query

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.ai_runs import AiRun, AiRunRepository
from backend.app.settings import Settings


def create_ai_observability_routes(
    settings: Settings,
    ai_runs_repository: AiRunRepository | None = None,
) -> APIRouter:
    """Create a router with AI observability endpoints."""

    def require_identity(
        identity_payload: str | None = Header(None, alias=ADMIN_IDENTITY_HEADER),
        signature: str | None = Header(None, alias=ADMIN_SIGNATURE_HEADER),
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(
            settings, identity_payload, signature
        )

    router = APIRouter(prefix="/admin/ai-observability")

    @router.get("/stats")
    async def get_stats(
        entity_type: str | None = Query(
            default=None,
            description="Filter by entity type (e.g. blog_idea, ai_news_scoring)",
        ),
        _identity: AdminIdentity = Depends(require_identity),
    ) -> dict:
        """Return aggregate AI run statistics."""
        if ai_runs_repository is None:
            return {
                "total_runs": 0,
                "completed": 0,
                "failed": 0,
                "success_rate": 0.0,
                "avg_latency_ms": 0.0,
                "avg_total_tokens": 0.0,
                "total_tokens": 0,
                "stages": {},
            }
        return ai_runs_repository.get_stats(entity_type=entity_type)

    @router.get("/cost-stats")
    async def get_cost_stats(
        _identity: AdminIdentity = Depends(require_identity),
    ) -> dict:
        """Return cost breakdown by model, stage, month, and entity."""
        if ai_runs_repository is None:
            return {
                "total_cost": 0.0,
                "avg_cost_per_run": 0.0,
                "cost_by_model": {},
                "cost_by_stage": {},
                "cost_by_month": {},
                "top_entities": [],
            }
        stats = ai_runs_repository.get_cost_stats()
        return stats.model_dump()

    @router.get("/runs")
    async def list_runs(
        limit: int = Query(default=50, ge=1, le=200),
        entity_type: str | None = Query(
            default=None,
            description="Filter by entity type",
        ),
        _identity: AdminIdentity = Depends(require_identity),
    ) -> list[AiRun]:
        """Return the most recent AI runs."""
        if ai_runs_repository is None:
            return []
        return ai_runs_repository.list_latest(
            limit=limit, entity_type=entity_type
        )

    return router
