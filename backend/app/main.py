# pyright: reportUnusedFunction=false
from typing import Annotated, cast

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.ai_runs import AiRunRepository, PostgresAiRunRepository
from backend.app.blog_claims import BlogClaimsRepository, PostgresBlogClaimsRepository
from backend.app.blog_ideas import BlogIdeaRepository, PostgresBlogIdeaRepository, create_blog_idea_routes
from backend.app.generation_jobs import GenerationJobRepository, PostgresGenerationJobRepository
from backend.app.news_crawl import NewsRawItemRepository, PostgresNewsRawItemRepository
from backend.app.news_extraction import ExtractedArticleRepository, PostgresExtractedArticleRepository
from backend.app.news_scoring import InMemoryNewsReviewRepository, NewsReviewRepository, PostgresNewsReviewRepository, create_news_review_routes
from backend.app.news_sources import NewsSourceRepository, PostgresNewsSourceRepository, create_news_source_routes
from backend.app.blog import (
    AdminBlogPostDetail,
    AdminBlogPostSummary,
    AuditEvent,
    BlogPost,
    BlogPostCreate,
    BlogPostDetail,
    BlogPostSummary,
    BlogPostUpdate,
    BlogRepository,
    PostgresBlogRepository,
)
from backend.app.database import create_database_engine
from backend.app.request_logging import RequestLoggingMiddleware
from backend.app.settings import Settings, get_settings
from backend.app.showcase import (
    AdminShowcaseDetail,
    AdminShowcaseSummary,
    PostgresShowcaseRepository,
    Showcase,
    ShowcaseCreate,
    ShowcaseDetail,
    ShowcaseRepository,
    ShowcaseSummary,
    ShowcaseUpdate,
)


def health(request: Request) -> dict[str, str]:  # pyright: ignore[reportUnusedFunction]
    settings = cast(Settings, request.app.state.settings)
    return {
        "service": settings.service_name,
        "status": "ok",
        "environment": settings.environment,
    }


def create_app(
    settings: Settings | None = None,
    blog_repository: BlogRepository | None = None,
    showcase_repository: ShowcaseRepository | None = None,
    blog_idea_repository: BlogIdeaRepository | None = None,
    generation_job_repository: GenerationJobRepository | None = None,
    claims_repository: BlogClaimsRepository | None = None,
    ai_run_repository: AiRunRepository | None = None,
    news_source_repository: NewsSourceRepository | None = None,
    news_raw_item_repository: NewsRawItemRepository | None = None,
    extracted_article_repository: ExtractedArticleRepository | None = None,
    news_review_repository: NewsReviewRepository | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    if resolved_settings.environment == "test":
        repository = blog_repository or BlogRepository()
        showcases_repo = showcase_repository or ShowcaseRepository()
        ideas_repo = blog_idea_repository or BlogIdeaRepository()
        jobs_repo = generation_job_repository or GenerationJobRepository()
        claims_repo = claims_repository or BlogClaimsRepository()
        ai_runs_repo = ai_run_repository or AiRunRepository()
        news_sources_repo = news_source_repository or NewsSourceRepository()
        news_raw_repo = news_raw_item_repository or NewsRawItemRepository()
        extracted_repo = extracted_article_repository or ExtractedArticleRepository()
        review_repo = news_review_repository or InMemoryNewsReviewRepository()
    else:
        engine = create_database_engine(resolved_settings)
        repository = blog_repository or PostgresBlogRepository(engine)
        showcases_repo = showcase_repository or PostgresShowcaseRepository(engine)
        ideas_repo = PostgresBlogIdeaRepository(engine)
        jobs_repo = generation_job_repository or PostgresGenerationJobRepository(engine)
        claims_repo = claims_repository or PostgresBlogClaimsRepository(engine)
        ai_runs_repo = ai_run_repository or PostgresAiRunRepository(engine)
        news_sources_repo = news_source_repository or PostgresNewsSourceRepository(engine)
        news_raw_repo = news_raw_item_repository or PostgresNewsRawItemRepository(engine)
        extracted_repo = extracted_article_repository or PostgresExtractedArticleRepository(engine)
        review_repo = news_review_repository or PostgresNewsReviewRepository(engine)

    app = FastAPI(title=resolved_settings.app_name)
    app.state.settings = resolved_settings
    app.add_middleware(RequestLoggingMiddleware)
    app.add_api_route("/health", health, methods=["GET"])

    def require_configured_admin_identity(
        identity_payload: Annotated[
            str | None, Header(alias=ADMIN_IDENTITY_HEADER)
        ] = None,
        signature: Annotated[str | None, Header(alias=ADMIN_SIGNATURE_HEADER)] = None,
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(
            resolved_settings, identity_payload, signature
        )

    def record_blog_audit(identity: AdminIdentity, action: str, post_id: str) -> None:
        repository.record_audit(
            actor_user_id=identity.user_id,
            actor_email=identity.email,
            action=action,
            entity_id=post_id,
        )

    ideas_router = create_blog_idea_routes(
        ideas_repo,
        resolved_settings,
        blog_repository=repository,
        record_blog_audit=record_blog_audit,
        jobs_repository=jobs_repo,
        claims_repository=claims_repo,
        ai_runs_repository=ai_runs_repo,
    )
    app.include_router(ideas_router)
    crawl_enqueue = None
    extract_enqueue = None
    rescore_enqueue = None
    if resolved_settings.environment != "test":
        from backend.app.tasks import crawl_rss_source_task, extract_raw_item_task, score_extracted_article_task

        def crawl_enqueue(source_id: str) -> str:
            return crawl_rss_source_task.delay(source_id).id

        def extract_enqueue(raw_item_id: str) -> str:
            return extract_raw_item_task.delay(raw_item_id).id

        def rescore_enqueue(extracted_article_id: str) -> str:
            return score_extracted_article_task.delay(extracted_article_id).id

    app.include_router(
        create_news_source_routes(
            news_sources_repo,
            resolved_settings,
            enqueue_rss_crawl=crawl_enqueue,
            enqueue_extract_raw_item=extract_enqueue,
            raw_items_repository=news_raw_repo,
            extracted_repository=extracted_repo,
            review_repository=review_repo,
        )
    )
    app.include_router(
        create_news_review_routes(
            review_repo,
            resolved_settings,
            extracted_repository=extracted_repo,
            raw_items_repository=news_raw_repo,
            sources_repository=news_sources_repo,
            enqueue_rescore=rescore_enqueue,
        )
    )

    def record_showcase_audit(
        identity: AdminIdentity, action: str, showcase_id: str
    ) -> None:
        showcases_repo.record_audit(
            actor_user_id=identity.user_id,
            actor_email=identity.email,
            action=action,
            entity_id=showcase_id,
        )

    @app.get("/admin/probe")
    async def admin_probe(
        identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> dict[str, str]:
        return {
            "status": "ok",
            "user_id": identity.user_id,
            "email": identity.email,
            "role": identity.role,
        }

    @app.get("/admin/blog-posts")
    async def admin_blog_posts(
        _identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> list[AdminBlogPostSummary]:
        return repository.list_all()

    @app.get("/admin/blog-posts/{post_id}")
    async def admin_blog_post(
        post_id: str,
        _identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> AdminBlogPostDetail:
        post = repository.get_by_id(post_id)
        if post is None:
            raise HTTPException(status_code=404, detail="Blog post not found")
        return post

    @app.post("/admin/blog-posts")
    async def create_blog_post(
        request: BlogPostCreate,
        identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> BlogPost:
        post = repository.create(request)
        record_blog_audit(identity, "blog_post.created", post.id)
        return post

    @app.patch("/admin/blog-posts/{post_id}")
    async def update_blog_post(
        post_id: str,
        request: BlogPostUpdate,
        identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> BlogPost:
        post = repository.update(post_id, request)
        if post is None:
            raise HTTPException(status_code=404, detail="Blog post not found")
        record_blog_audit(identity, "blog_post.updated", post.id)
        return post

    @app.post("/admin/blog-posts/{post_id}/publish")
    async def publish_blog_post(
        post_id: str,
        identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> BlogPost:
        post = repository.publish(post_id)
        if post is None:
            raise HTTPException(status_code=404, detail="Blog post not found")
        record_blog_audit(identity, "blog_post.published", post.id)
        return post

    @app.post("/admin/blog-posts/{post_id}/unpublish")
    async def unpublish_blog_post(
        post_id: str,
        identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> BlogPost:
        post = repository.unpublish(post_id)
        if post is None:
            raise HTTPException(status_code=404, detail="Blog post not found")
        record_blog_audit(identity, "blog_post.unpublished", post.id)
        return post

    @app.get("/admin/showcases")
    async def admin_showcases(
        _identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> list[AdminShowcaseSummary]:
        return showcases_repo.list_all()

    @app.get("/admin/showcases/{showcase_id}")
    async def admin_showcase(
        showcase_id: str,
        _identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> AdminShowcaseDetail:
        item = showcases_repo.get_by_id(showcase_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Showcase not found")
        return item

    @app.post("/admin/showcases")
    async def create_showcase(
        request: ShowcaseCreate,
        identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> Showcase:
        item = showcases_repo.create(request)
        record_showcase_audit(identity, "showcase.created", item.id)
        return item

    @app.patch("/admin/showcases/{showcase_id}")
    async def update_showcase(
        showcase_id: str,
        request: ShowcaseUpdate,
        identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> Showcase:
        item = showcases_repo.update(showcase_id, request)
        if item is None:
            raise HTTPException(status_code=404, detail="Showcase not found")
        record_showcase_audit(identity, "showcase.updated", item.id)
        return item

    @app.post("/admin/showcases/{showcase_id}/publish")
    async def publish_showcase(
        showcase_id: str,
        identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> Showcase:
        item = showcases_repo.publish(showcase_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Showcase not found")
        record_showcase_audit(identity, "showcase.published", item.id)
        return item

    @app.post("/admin/showcases/{showcase_id}/unpublish")
    async def unpublish_showcase(
        showcase_id: str,
        identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> Showcase:
        item = showcases_repo.unpublish(showcase_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Showcase not found")
        record_showcase_audit(identity, "showcase.unpublished", item.id)
        return item

    @app.get("/admin/audit-events")
    async def admin_audit_events(
        _identity: AdminIdentity = Depends(require_configured_admin_identity),
    ) -> list[AuditEvent]:
        return repository.list_audit_events()

    @app.get("/public/blog-posts")
    async def public_blog_posts() -> list[BlogPostSummary]:
        return repository.list_published()

    @app.get("/public/blog-posts/{slug}")
    async def public_blog_post(slug: str) -> BlogPostDetail:
        post = repository.get_published_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=404, detail="Published blog post not found")
        return post

    @app.get("/public/showcases")
    async def public_showcases() -> list[ShowcaseSummary]:
        return showcases_repo.list_published()

    @app.get("/public/showcases/{slug}")
    async def public_showcase(slug: str) -> ShowcaseDetail:
        item = showcases_repo.get_published_by_slug(slug)
        if item is None:
            raise HTTPException(status_code=404, detail="Published showcase not found")
        return item

    return app


app = create_app()
