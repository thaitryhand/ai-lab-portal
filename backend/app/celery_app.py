from celery import Celery

from backend.app.settings import Settings


def create_celery_app(settings: Settings | None = None) -> Celery:
    resolved_settings = settings or Settings()
    redis_url = str(resolved_settings.redis_url)

    celery_app = Celery(
        "ai_lab_portal",
        broker=redis_url,
        backend=redis_url,
        include=["backend.app.tasks"],
    )
    celery_app.conf.update(
        task_default_queue="ai_lab_portal",
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        beat_schedule={
            "publish-scheduled-posts": {
                "task": "blog.publish_scheduled_posts",
                "schedule": 900.0,  # every 15 minutes
            },
            "crawl-due-rss-sources": {
                "task": "news.crawl_due_sources",
                "schedule": 1800.0,  # every 30 minutes
            },
            "fetch-due-github-sources": {
                "task": "news.fetch_due_github_sources",
                "schedule": 3600.0,  # every 60 minutes
            },
            "extract-pending-raw-items": {
                "task": "news.extract_pending_raw_items",
                "schedule": 900.0,  # every 15 minutes
            },
            "ingest-due-hackernews-sources": {
                "task": "news.ingest_due_hackernews_sources",
                "schedule": 900.0,  # every 15 minutes
            },
            "score-pending-extractions": {
                "task": "news.score_pending_extractions",
                "schedule": 900.0,  # every 15 minutes
            },
        },
    )
    if resolved_settings.llm_e2e_fake or resolved_settings.environment == "test":
        celery_app.conf.task_always_eager = True
        celery_app.conf.task_eager_propagates = True
    return celery_app


celery_app = create_celery_app()
