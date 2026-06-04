# pyright: reportUnusedFunction=false
from collections.abc import Callable
from typing import Annotated, Any, cast

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.ai_runs import AiRunRepository, PostgresAiRunRepository
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
    BlogRepositoryProtocol,
    PostgresBlogRepository,
)
from backend.app.blog_claims import BlogClaimsRepository, PostgresBlogClaimsRepository
from backend.app.blog_ideas import (
    BlogIdeaRepository,
    PostgresBlogIdeaRepository,
    create_blog_idea_routes,
)
from backend.app.blog_social import (
    BlogSocialRepository,
    InMemoryBlogSocialRepository,
    PostgresBlogSocialRepository,
    create_blog_social_routes,
    create_blog_social_admin_routes,
    create_user_bookmarks_routes,
)
from backend.app.blog_tags import (
    BlogTagRepository,
    InMemoryBlogTagRepository,
    PostgresBlogTagRepository,
    create_blog_tag_admin_routes,
    create_blog_tag_routes,
)
from backend.app.database import create_database_engine
from backend.app.generation_jobs import (
    GenerationJobRepository,
    PostgresGenerationJobRepository,
)
from backend.app.news_crawl import NewsRawItemRepository, PostgresNewsRawItemRepository
from backend.app.news_extraction import (
    ExtractedArticleRepository,
    PostgresExtractedArticleRepository,
)
from backend.app.news_publish import (
    PublicAiNewsDetail,
    PublicAiNewsSummary,
    get_public_ai_news_by_slug,
    list_public_ai_news,
)
from backend.app.news_scoring import (
    InMemoryNewsReviewRepository,
    NewsReviewRepository,
    PostgresNewsReviewRepository,
    create_news_review_routes,
)
from backend.app.news_sources import (
    NewsSourceRepository,
    PostgresNewsSourceRepository,
    create_news_source_routes,
)
from backend.app.news_submitted_links import (
    InMemorySubmittedLinkRepository,
    PostgresSubmittedLinkRepository,
    SubmittedLinkRepository,
    create_public_submitted_link_route,
    create_submitted_link_routes,
)
from backend.app.request_logging import RequestLoggingMiddleware
from backend.app.settings import Settings, get_settings
from backend.app.user_profiles import (
    InMemoryUserProfileRepository,
    PostgresUserProfileRepository,
    UserProfileRepository,
    create_user_profile_admin_routes,
    create_user_profile_routes,
)
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
    blog_repository: BlogRepositoryProtocol | None = None,
    showcase_repository: ShowcaseRepository | None = None,
    blog_idea_repository: BlogIdeaRepository | None = None,
    generation_job_repository: GenerationJobRepository | None = None,
    claims_repository: BlogClaimsRepository | None = None,
    ai_run_repository: AiRunRepository | None = None,
    news_source_repository: NewsSourceRepository | None = None,
    news_raw_item_repository: NewsRawItemRepository | None = None,
    extracted_article_repository: ExtractedArticleRepository | None = None,
    news_review_repository: NewsReviewRepository | None = None,
    submitted_link_repository: SubmittedLinkRepository | None = None,
    blog_social_repository: BlogSocialRepository | None = None,
    blog_tag_repository: BlogTagRepository | None = None,
    user_profile_repository: UserProfileRepository | None = None,
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
        submitted_repo = submitted_link_repository or InMemorySubmittedLinkRepository()
        social_repo = blog_social_repository or InMemoryBlogSocialRepository()
        tag_repo = blog_tag_repository or InMemoryBlogTagRepository()
        profile_repo = user_profile_repository or InMemoryUserProfileRepository()
    else:
        engine = create_database_engine(resolved_settings)
        repository = blog_repository or PostgresBlogRepository(engine)
        showcases_repo = showcase_repository or PostgresShowcaseRepository(engine)
        ideas_repo = PostgresBlogIdeaRepository(engine)
        jobs_repo = generation_job_repository or PostgresGenerationJobRepository(engine)
        claims_repo = claims_repository or PostgresBlogClaimsRepository(engine)
        ai_runs_repo = ai_run_repository or PostgresAiRunRepository(engine)
        news_sources_repo = news_source_repository or PostgresNewsSourceRepository(
            engine
        )
        news_raw_repo = news_raw_item_repository or PostgresNewsRawItemRepository(
            engine
        )
        extracted_repo = (
            extracted_article_repository or PostgresExtractedArticleRepository(engine)
        )
        review_repo = news_review_repository or PostgresNewsReviewRepository(engine)
        submitted_repo = submitted_link_repository or PostgresSubmittedLinkRepository(
            engine
        )
        social_repo = blog_social_repository or PostgresBlogSocialRepository(engine)
        tag_repo = blog_tag_repository or PostgresBlogTagRepository(engine)
        profile_repo = user_profile_repository or PostgresUserProfileRepository(engine)

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
    crawl_enqueue: Callable[[str], str] | None = None
    extract_enqueue: Callable[[str], str] | None = None
    rescore_enqueue: Callable[[str], str] | None = None
    process_submission_enqueue: Callable[[str], str] | None = None
    if resolved_settings.environment != "test":
        from backend.app.tasks import (
            crawl_rss_source_task,
            extract_raw_item_task,
            process_submitted_link_task,
            score_extracted_article_task,
        )

        def _crawl_enqueue(source_id: str) -> str:
            return cast(Any, crawl_rss_source_task).delay(source_id).id

        def _extract_enqueue(raw_item_id: str) -> str:
            return cast(Any, extract_raw_item_task).delay(raw_item_id).id

        def _rescore_enqueue(extracted_article_id: str) -> str:
            return (
                cast(Any, score_extracted_article_task).delay(extracted_article_id).id
            )

        def _process_submission_enqueue(submission_id: str) -> str:
            return cast(Any, process_submitted_link_task).delay(submission_id).id

        crawl_enqueue = _crawl_enqueue
        extract_enqueue = _extract_enqueue
        rescore_enqueue = _rescore_enqueue
        process_submission_enqueue = _process_submission_enqueue

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
    app.include_router(
        create_submitted_link_routes(
            submitted_repo,
            resolved_settings,
            extracted_repository=extracted_repo,
            raw_items_repository=news_raw_repo,
            sources_repository=news_sources_repo,
            review_repository=review_repo,
            enqueue_process=process_submission_enqueue,
        )
    )
    app.include_router(
        create_public_submitted_link_route(
            submitted_repo,
            enqueue_process=process_submission_enqueue,
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
    async def public_blog_posts(tag: str | None = None) -> list[BlogPostSummary]:
        post_ids = tag_repo.get_post_ids_for_tag_slug(tag) if tag else None
        return repository.list_published(post_ids=post_ids)

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

    @app.get("/public/ai-news")
    async def public_ai_news(topic: str | None = None) -> list[PublicAiNewsSummary]:
        return list_public_ai_news(
            review=review_repo,
            extracted=extracted_repo,
            sources=news_sources_repo,
            topic=topic,
        )

    @app.get("/public/ai-news/{slug}")
    async def public_ai_news_item(slug: str) -> PublicAiNewsDetail:
        item = get_public_ai_news_by_slug(
            slug,
            review=review_repo,
            extracted=extracted_repo,
            sources=news_sources_repo,
        )
        if item is None:
            raise HTTPException(
                status_code=404, detail="Published AI news item not found"
            )
        return item

    # Blog tag taxonomy
    app.include_router(create_blog_tag_routes(tag_repo, repository))
    app.include_router(create_blog_tag_admin_routes(tag_repo, resolved_settings))

    # User profiles
    app.include_router(create_user_profile_routes(profile_repo, resolved_settings))
    app.include_router(create_user_profile_admin_routes(profile_repo, resolved_settings))

    # Blog social features (reactions, bookmarks, comments)
    app.include_router(
        create_blog_social_routes(
            social_repo,
            repository,
            resolved_settings,
            profile_repo,
        )
    )
    app.include_router(
        create_blog_social_admin_routes(
            social_repo,
            repository,
            resolved_settings,
        )
    )
    app.include_router(
        create_user_bookmarks_routes(
            social_repo,
            repository,
            resolved_settings,
        )
    )

    return app


app = create_app()
