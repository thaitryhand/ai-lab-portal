"""Tests for KnowledgeService and KnowledgeContextRepository."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from backend.app.knowledge_collector import InMemoryKnowledgeService, KnowledgeCollectionResult, KnowledgeService
from backend.app.knowledge_context import (
    InMemoryKnowledgeContextRepository,
    KnowledgeContext,
    KnowledgeContextUpdate,
    RelatedPost,
    RelatedShowcase,
)


class TestKnowledgeService:
    """KnowledgeService basic functionality (in-memory mode)."""

    def test_collect_for_project_returns_context(self):
        ks = InMemoryKnowledgeService()
        result = ks.collect_for_project(
            project_name="Test Project",
            project_summary="A test project",
            project_content="## Content\nTest content here.",
        )
        assert isinstance(result, KnowledgeCollectionResult)
        assert result.sources_queried >= 1
        assert "Test Project" in result.context_summary
        assert "A test project" in result.context_summary

    def test_collect_for_project_empty_content(self):
        ks = InMemoryKnowledgeService()
        result = ks.collect_for_project(project_name="Empty")
        assert result.sources_queried >= 1
        assert "Empty" in result.context_summary

    def test_collect_for_idea_returns_string(self):
        ks = InMemoryKnowledgeService()
        result = ks.collect_for_idea("idea-123", "Test Project")
        assert isinstance(result, str)
        assert "Test Project" in result

    def test_to_prompt_context_empty(self):
        result = KnowledgeCollectionResult()
        prompt = result.to_prompt_context()
        assert prompt == ""

    def test_to_prompt_context_with_data(self):
        result = KnowledgeCollectionResult(
            sources_queried=2,
            blog_posts_found=3,
            context_summary="Project: My Project\nDescription: A project.",
        )
        prompt = result.to_prompt_context()
        assert "My Project" in prompt
        assert "Related blog posts available: 3" in prompt

    def test_round_trip_via_knowledge_service(self):
        ks = InMemoryKnowledgeService()
        result = ks.collect_for_project(
            project_name="AI Platform",
            project_summary="An AI platform for testing",
            project_content="Content about the AI platform",
        )
        assert result.blog_posts_found >= 0
        assert result.showcases_found >= 0
        prompt = result.to_prompt_context()
        assert "AI Platform" in prompt


class TestKnowledgeContextRepository:
    """KnowledgeContextRepository (InMemory) basic operations."""

    @pytest.fixture
    def repo(self):
        return InMemoryKnowledgeContextRepository()

    @pytest.fixture
    def sample_context(self):
        now = datetime.now(UTC)
        return KnowledgeContext(
            id=str(uuid4()),
            blog_idea_id="idea-test-1",
            project_name="Test Project",
            project_summary="A summary",
            related_blog_posts=[RelatedPost(title="Post 1", excerpt="Excerpt 1", slug="post-1")],
            related_showcases=[RelatedShowcase(title="Showcase 1", summary="Summary 1", slug="showcase-1")],
            raw_collected_at=now,
            created_at=now,
            updated_at=now,
        )

    def test_create_and_get(self, repo, sample_context):
        repo.upsert(sample_context)
        retrieved = repo.get_by_idea_id("idea-test-1")
        assert retrieved is not None
        assert retrieved.project_name == "Test Project"
        assert len(retrieved.related_blog_posts) == 1
        assert retrieved.related_blog_posts[0].title == "Post 1"

    def test_get_nonexistent(self, repo):
        retrieved = repo.get_by_idea_id("nonexistent")
        assert retrieved is None

    def test_update_fields(self, repo, sample_context):
        repo.upsert(sample_context)
        updated = repo.update_fields("idea-test-1", KnowledgeContextUpdate(project_summary="Updated summary"))
        assert updated is not None
        assert updated.project_summary == "Updated summary"
        assert updated.edited_at is not None

    def test_approve(self, repo, sample_context):
        repo.upsert(sample_context)
        approved = repo.approve("idea-test-1", approved_by="admin-user")
        assert approved is not None
        assert approved.approved_at is not None
        assert approved.approved_by == "admin-user"

    def test_approve_nonexistent(self, repo):
        approved = repo.approve("nonexistent", approved_by="admin")
        assert approved is None

    def test_delete(self, repo, sample_context):
        repo.upsert(sample_context)
        repo.delete_by_idea_id("idea-test-1")
        assert repo.get_by_idea_id("idea-test-1") is None

    def test_upsert_updates_existing(self, repo, sample_context):
        repo.upsert(sample_context)
        now = datetime.now(UTC)
        updated_ctx = KnowledgeContext(
            id=sample_context.id,
            blog_idea_id="idea-test-1",
            project_name="Updated Project",
            raw_collected_at=now,
            created_at=now,
            updated_at=now,
        )
        repo.upsert(updated_ctx)
        retrieved = repo.get_by_idea_id("idea-test-1")
        assert retrieved.project_name == "Updated Project"
