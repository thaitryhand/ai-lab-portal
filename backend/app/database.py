from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, MetaData, String, Table, Text, UniqueConstraint, create_engine
from sqlalchemy.engine import Engine

from backend.app.settings import Settings

metadata = MetaData()


def create_database_engine(settings: Settings) -> Engine:
    return create_engine(str(settings.database_url), pool_pre_ping=True)

blog_posts = Table(
    "blog_posts",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("slug", String(160), nullable=False, unique=True),
    Column("title", String(240), nullable=False),
    Column("excerpt", Text, nullable=False),
    Column("author_name", String(120), nullable=False),
    Column("status", String(32), nullable=False),
    Column("published_at", DateTime(timezone=True), nullable=True),
    Column("content_markdown", Text, nullable=False),
)

showcases = Table(
    "showcases",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("slug", String(160), nullable=False, unique=True),
    Column("title", String(240), nullable=False),
    Column("hero_summary", Text, nullable=False),
    Column("industry", String(120), nullable=True),
    Column("use_case", String(240), nullable=True),
    Column("status", String(32), nullable=False),
    Column("published_at", DateTime(timezone=True), nullable=True),
    Column("content_markdown", Text, nullable=False),
    Index("ix_showcases_status_published_at", "status", "published_at"),
)

audit_events = Table(
    "audit_events",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("actor_user_id", String(128), nullable=False),
    Column("actor_email", String(320), nullable=False),
    Column("action", String(80), nullable=False),
    Column("entity_type", String(80), nullable=False),
    Column("entity_id", String(128), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_audit_events_entity", "entity_type", "entity_id"),
    Index("ix_audit_events_actor", "actor_user_id"),
)

blog_ideas = Table(
    "blog_ideas",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("title", String(240), nullable=False),
    Column("angle", String(160), nullable=False),
    Column("target_reader", String(160), nullable=False),
    Column("article_goal", Text, nullable=False),
    Column("positioning_notes", Text, nullable=True),
    Column("source", String(32), nullable=False),
    Column("source_project_context", Text, nullable=True),
    Column("status", String(32), nullable=False),
    Column("reviewed_by", String(128), nullable=True),
    Column("reviewed_at", DateTime(timezone=True), nullable=True),
    Column("feedback", Text, nullable=True),
    Column("outline_sections", Text, nullable=True),
    Column("outline_status", String(32), nullable=True),
    Column("draft_markdown", Text, nullable=True),
    Column("draft_status", String(32), nullable=True),
    Column("technical_review", Text, nullable=True),
    Column("technical_review_status", String(32), nullable=True),
    Column("marketing_metadata", Text, nullable=True),
    Column("marketing_status", String(32), nullable=True),
    Column("published_blog_post_id", String(64), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_blog_ideas_status", "status"),
    Index("ix_blog_ideas_created_at", "created_at"),
    Index("ix_blog_ideas_outline_status", "outline_status"),
    Index("ix_blog_ideas_draft_status", "draft_status"),
    Index("ix_blog_ideas_review_status", "technical_review_status"),
    Index("ix_blog_ideas_marketing_status", "marketing_status"),
    Index("ix_blog_ideas_published_blog_post_id", "published_blog_post_id"),
)

ai_runs = Table(
    "ai_runs",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("prompt_name", String(80), nullable=False),
    Column("prompt_version", String(32), nullable=False),
    Column("entity_type", String(64), nullable=False),
    Column("entity_id", String(64), nullable=False),
    Column("provider", String(32), nullable=False),
    Column("model", String(80), nullable=False),
    Column("status", String(32), nullable=False),
    Column("input_payload", Text, nullable=False),
    Column("output_payload", Text, nullable=True),
    Column("error_message", Text, nullable=True),
    Column("prompt_tokens", Integer, nullable=True),
    Column("completion_tokens", Integer, nullable=True),
    Column("total_tokens", Integer, nullable=True),
    Column("latency_ms", Integer, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_ai_runs_entity", "entity_type", "entity_id"),
    Index("ix_ai_runs_prompt", "prompt_name", "created_at"),
)

blog_generation_jobs = Table(
    "blog_generation_jobs",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("blog_idea_id", String(64), nullable=False),
    Column("stage", String(32), nullable=False),
    Column("celery_task_id", String(128), nullable=False),
    Column("status", String(32), nullable=False),
    Column("error_message", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_blog_generation_jobs_idea", "blog_idea_id", "created_at"),
    Index("ix_blog_generation_jobs_celery_task_id", "celery_task_id", unique=True),
)

blog_claims = Table(
    "blog_claims",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("blog_idea_id", String(64), nullable=False),
    Column("claim_text", Text, nullable=False),
    Column("claim_type", String(32), nullable=False),
    Column("status", String(32), nullable=False),
    Column("evidence_source_type", String(32), nullable=True),
    Column("evidence_reference", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_blog_claims_idea", "blog_idea_id"),
)

news_sources = Table(
    "news_sources",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("name", String(160), nullable=False),
    Column("source_type", String(32), nullable=False),
    Column("url_or_identifier", String(512), nullable=False),
    Column("description", Text, nullable=True),
    Column("priority", String(16), nullable=False),
    Column("crawl_frequency_minutes", Integer, nullable=False),
    Column("is_enabled", Boolean, nullable=False),
    Column("credibility_base_score", Float, nullable=False),
    Column("last_crawled_at", DateTime(timezone=True), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Index("ix_news_sources_enabled", "is_enabled"),
    Index("ix_news_sources_type", "source_type"),
)

news_raw_items = Table(
    "news_raw_items",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("source_id", String(64), ForeignKey("news_sources.id", ondelete="CASCADE"), nullable=False),
    Column("external_id", String(512), nullable=False),
    Column("title", String(512), nullable=False),
    Column("link_url", String(1024), nullable=False),
    Column("published_at", DateTime(timezone=True), nullable=True),
    Column("raw_payload", Text, nullable=False),
    Column("content_hash", String(64), nullable=False),
    Column("fetched_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("source_id", "external_id", name="uq_news_raw_items_source_external"),
    Index("ix_news_raw_items_source", "source_id"),
    Index("ix_news_raw_items_fetched", "fetched_at"),
)
