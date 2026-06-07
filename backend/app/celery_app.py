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
        },
    )
    if resolved_settings.llm_e2e_fake or resolved_settings.environment == "test":
        celery_app.conf.task_always_eager = True
        celery_app.conf.task_eager_propagates = True
    return celery_app


celery_app = create_celery_app()
