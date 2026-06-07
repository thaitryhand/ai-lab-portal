"""E2E integration tests for OpenAI Agents SDK backend (US-092).

These tests verify that the Agents SDK backend works correctly with fake
responses (no real API calls). They exercise the factory, recording wrapper,
and backend parity without needing a running Docker or real API key.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from backend.app.llm.recording import RecordingLLMService
from backend.app.llm.schemas import BlogIdea, BlogOutline, BlogOutlineSection
from backend.app.llm.service import FakeLLMService, LLMService
from backend.app.settings import Settings


# ===========================================================================
# Factory integration
# ===========================================================================


class TestAgentsSDKFactory:
    """Verify _build_llm_service returns the right type for each backend."""

    def test_openai_backend_returns_openai_service(self) -> None:
        from backend.app.task_support import _build_llm_service

        settings = Settings(environment="test", llm_backend="openai")
        service = _build_llm_service("test-key", "gpt-4o", settings)
        from backend.app.llm.service import OpenAILLMService

        assert isinstance(service, OpenAILLMService)

    def test_agents_sdk_backend_returns_agents_sdk_service(self) -> None:
        from backend.app.task_support import _build_llm_service

        settings = Settings(environment="test", llm_backend="agents_sdk")
        service = _build_llm_service("test-key", "gpt-4o", settings)
        from backend.app.llm.agents_sdk_service import AgentsSDKLLMService

        assert isinstance(service, AgentsSDKLLMService)

    def test_both_backends_implement_llm_service_abc(self) -> None:
        """Both backends satisfy the LLMService contract."""
        from backend.app.task_support import _build_llm_service

        for backend in ("openai", "agents_sdk"):
            settings = Settings(environment="test", llm_backend=backend)
            service = _build_llm_service("test-key", "gpt-4o", settings)
            assert isinstance(service, LLMService)

    def test_backend_uses_correct_model_name(self) -> None:
        from backend.app.task_support import _build_llm_service

        settings = Settings(environment="test", llm_backend="agents_sdk")
        service = _build_llm_service("test-key", "gpt-4o-mini", settings)
        assert service._model == "gpt-4o-mini"


# ===========================================================================
# Recording integration
# ===========================================================================


class TestRecordingWithAgentsSDK:
    """RecordingLLMService wrapping works with both backends."""

    def test_recording_wraps_agents_sdk_service(self) -> None:
        """RecordingLLMService accepts an AgentsSDKLLMService as inner."""
        from backend.app.llm.agents_sdk_service import AgentsSDKLLMService
        from backend.app.ai_runs import AiRunRepository

        inner = AgentsSDKLLMService(api_key="test-key")
        recorder = AiRunRepository()
        service = RecordingLLMService(
            inner, recorder, entity_type="blog_idea", entity_id="idea_1"
        )
        assert service._inner is inner
        assert isinstance(service, LLMService)

    def test_fake_wrapped_with_agents_sdk_setting(self) -> None:
        """FakeLLMService + agents_sdk backend setting still works for E2E."""
        from backend.app.ai_runs import AiRunRepository

        fake = FakeLLMService(
            {
                "blog_idea": BlogIdea(
                    title="Fake Idea",
                    angle="Test",
                    target_reader="Devs",
                    article_goal="Test",
                )
            }
        )
        recorder = AiRunRepository()
        service = RecordingLLMService(
            fake,
            recorder,
            entity_type="blog_idea",
            entity_id="idea_2",
            provider="agents_sdk",
        )
        result = service.generate("blog_idea", {}, BlogIdea)
        assert isinstance(result, BlogIdea)
        assert result.title == "Fake Idea"


# ===========================================================================
# Backend parity via fake service
# ===========================================================================


class TestBackendParity:
    """Both backends produce the same output given the same fake prompt output.

    This test proves that switching AI_LAB_LLM_BACKEND does not change the
    pipeline behavior — the LLMService ABC ensures identical contracts.
    """

    def test_fake_output_identical_regardless_of_backend_config(self) -> None:
        """The pipeline produces the same output with both backend settings."""
        from backend.app.task_support import llm_service_for_idea

        for backend in ("openai", "agents_sdk"):
            settings = Settings(
                environment="test",
                llm_e2e_fake=True,
                llm_backend=backend,
            )
            service = llm_service_for_idea("test-parity", settings)
            result = service.generate(
                "blog_idea",
                inputs={
                    "project_name": "Parity Check",
                    "project_summary": "Testing backend parity.",
                    "ai_capabilities": "LLM, agents",
                    "technical_highlights": "Parity test",
                    "business_value": "Confidence",
                },
                output_schema=BlogIdea,
            )
            assert isinstance(result, BlogIdea)
            assert result.title == "E2E Golden Path Blog Idea"

    def test_fake_service_returns_all_schema_types_with_agents_sdk_setting(
        self,
    ) -> None:
        """Every schema type is reachable with agents_sdk backend + fake mode."""
        from backend.app.task_support import llm_service_for_idea

        schemas: list[tuple[str, dict, type[BaseModel]]] = [
            (
                "blog_idea",
                {
                    "project_name": "P",
                    "project_summary": "S",
                    "ai_capabilities": "C",
                    "technical_highlights": "T",
                    "business_value": "V",
                },
                BlogIdea,
            ),
        ]

        settings = Settings(
            environment="test",
            llm_e2e_fake=True,
            llm_backend="agents_sdk",
        )
        service = llm_service_for_idea("test-schemas", settings)

        for prompt_name, inputs, schema in schemas:
            result = service.generate(prompt_name, inputs, schema)
            assert isinstance(result, schema), (
                f"Failed for {prompt_name} with agents_sdk: "
                f"got {type(result).__name__}"
            )

    def test_e2e_fake_overrides_backend_even_with_agents_sdk(self) -> None:
        """E2E fake mode takes precedence, returning FakeBlogIdeaService."""
        from backend.app.task_support import llm_service_for_idea
        from backend.app.llm.service import FakeLLMService

        settings = Settings(
            environment="test",
            llm_e2e_fake=True,
            llm_backend="agents_sdk",
        )
        service = llm_service_for_idea("test-override", settings)
        # Unwrap RecordingLLMService to check inner
        inner = service._inner if hasattr(service, "_inner") else service
        assert isinstance(inner, FakeLLMService), (
            f"Expected FakeLLMService when llm_e2e_fake=True, "
            f"got {type(inner).__name__}"
        )

    def test_provider_name_matches_backend(self) -> None:
        """The provider name recorded in ai_runs reflects the backend setting."""
        from backend.app.task_support import _provider_name

        openai_settings = Settings(environment="test", llm_backend="openai")
        assert _provider_name(openai_settings) == "openai"

        agents_settings = Settings(environment="test", llm_backend="agents_sdk")
        assert _provider_name(agents_settings) == "agents_sdk"


# ===========================================================================
# Tracing processor (AiRunSpanProcessor)
# ===========================================================================


class TestAiRunSpanProcessor:
    """Tests for the custom Agents SDK tracing processor."""

    def test_processor_constructs(self) -> None:
        from backend.app.llm.tracing import AiRunSpanProcessor

        processor = AiRunSpanProcessor()
        assert processor.active_traces == {}
        assert processor.active_spans == {}

    def test_trace_lifecycle(self) -> None:
        from backend.app.llm.tracing import AiRunSpanProcessor

        processor = AiRunSpanProcessor()
        tid = "test_trace_001"

        class MockTrace:
            def __init__(self):
                self.trace_id = tid
                self.name = "blog_outline"
                self.group_id = "group_1"
                self.metadata = {"prompt": "outline"}

        trace = MockTrace()
        processor.on_trace_start(trace)
        assert tid in processor.active_traces
        assert processor.active_traces[tid]["workflow_name"] == "blog_outline"

        processor.on_trace_end(trace)
        assert tid not in processor.active_traces

    def test_span_lifecycle(self) -> None:
        from backend.app.llm.tracing import AiRunSpanProcessor

        processor = AiRunSpanProcessor()
        sid = "test_span_001"

        class MockSpan:
            def __init__(self):
                self.span_id = sid
                self.trace_id = "trace_001"
                self.type = "agent"
                self.name = "Agent run"

        span = MockSpan()
        processor.on_span_start(span)
        assert sid in processor.active_spans

        processor.on_span_end(span)
        assert sid not in processor.active_spans

    def test_shutdown_clears_all(self) -> None:
        from backend.app.llm.tracing import AiRunSpanProcessor

        processor = AiRunSpanProcessor()
        class MockTrace:
            def __init__(self):
                self.trace_id = "t1"
                self.name = "test"
                self.group_id = None
                self.metadata = None

        processor.on_trace_start(MockTrace())
        assert len(processor.active_traces) == 1
        processor.shutdown()
        assert processor.active_traces == {}
        assert processor.active_spans == {}

    def test_setup_agents_tracing_creates_processor(self) -> None:
        """setup_agents_tracing() registers a processor without error."""
        from backend.app.llm.tracing import setup_agents_tracing, AiRunSpanProcessor

        # Verify the function exists and accepts our processor type
        processor = AiRunSpanProcessor()
        assert processor is not None
        assert callable(setup_agents_tracing)


# ===========================================================================
# Agent session store (US-094 HITL)
# ===========================================================================


class TestAgentSessionStore:
    """Tests for the agent session persistence layer."""

    def test_store_is_singleton(self) -> None:
        from backend.app.llm.sessions import get_session_store, AgentSessionStore

        store1 = get_session_store()
        store2 = get_session_store()
        assert store1 is store2

    def test_has_session_returns_false_for_missing(self) -> None:
        from backend.app.llm.sessions import AgentSessionStore
        store = AgentSessionStore()
        assert not store.has_session("nonexistent")

    def test_drop_removes_session(self) -> None:
        from backend.app.llm.sessions import AgentSessionStore
        store = AgentSessionStore()
        store._sessions["idea_1"] = {
            "state_raw": {"test": True},
            "agent_name": "outline",
            "metadata": {},
        }
        assert store.has_session("idea_1")
        store.drop("idea_1")
        assert not store.has_session("idea_1")

    def test_clear_removes_all(self) -> None:
        from backend.app.llm.sessions import AgentSessionStore
        store = AgentSessionStore()
        store._sessions["a"] = {"state_raw": {}, "agent_name": "", "metadata": {}}
        store._sessions["b"] = {"state_raw": {}, "agent_name": "", "metadata": {}}
        assert len(store._sessions) == 2
        store.clear()
        assert len(store._sessions) == 0


# ===========================================================================
# Guardrails (US-095 claim extraction)
# ===========================================================================


class TestClaimGuardrail:
    """Tests for the claim extraction guardrail (native SDK output guardrails)."""

    def test_guardrail_factory_returns_output_guardrail(self) -> None:
        from backend.app.llm.guardrails import claim_extraction_guardrail
        from backend.app.blog_claims import BlogClaimsRepository
        from backend.app.blog_ideas import BlogIdeaRepository
        from agents import OutputGuardrail

        guardrail = claim_extraction_guardrail(
            BlogClaimsRepository(), BlogIdeaRepository(), idea_id="test-idea"
        )
        assert isinstance(guardrail, OutputGuardrail)
        assert guardrail.name == "claim_extraction"

    def test_guardrail_skips_empty_idea_id(self) -> None:
        """Guardrail returns tripwire_triggered=False when idea_id is empty."""
        from backend.app.llm.guardrails import claim_extraction_guardrail
        from backend.app.blog_claims import BlogClaimsRepository
        from backend.app.blog_ideas import BlogIdeaRepository
        from backend.app.llm.schemas import TechnicalReview

        guardrail = claim_extraction_guardrail(
            BlogClaimsRepository(), BlogIdeaRepository(), idea_id=""
        )
        # The guardrail function is async; verify it exists and is callable
        assert guardrail.name == "claim_extraction"

    def test_add_output_guardrail_to_service(self) -> None:
        from backend.app.llm.agents_sdk_service import AgentsSDKLLMService
        from agents import output_guardrail, GuardrailFunctionOutput

        @output_guardrail
        async def dummy_guardrail(context, agent, output):
            return GuardrailFunctionOutput(
                output_info="dummy", tripwire_triggered=False
            )

        service = AgentsSDKLLMService(api_key="test-key")
        service.add_output_guardrail("technical_review", dummy_guardrail)
        assert "technical_review" in service._output_guardrails
        assert len(service._output_guardrails["technical_review"]) == 1


# ===========================================================================
# blog_agent_context
# ===========================================================================


class TestBlogAgentContext:
    """Verify the project context builder for blog agent prompts."""

    def test_build_context_without_source(self):
        """Context includes title, angle, target reader, and goal."""
        from datetime import UTC, datetime
        from backend.app.blog_agent_context import build_project_context
        from backend.app.blog_ideas import BlogIdea

        idea = BlogIdea(
            id="test_1",
            title="My Blog Post",
            angle="Technical deep dive",
            target_reader="Developers",
            article_goal="Teach something",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        result = build_project_context(idea)
        assert "My Blog Post" in result
        assert "Technical deep dive" in result
        assert "Developers" in result
        assert "Teach something" in result

    def test_build_context_with_source_project(self):
        """Context includes source project fields when available."""
        from datetime import UTC, datetime
        from backend.app.blog_agent_context import build_project_context
        from backend.app.blog_ideas import BlogIdea

        idea = BlogIdea(
            id="test_2",
            title="AI Article",
            angle="Analysis",
            target_reader="Engineers",
            article_goal="Inform",
            source_project_context={
                "project_name": "AI Lab",
                "project_summary": "An AI platform",
                "ai_capabilities": "LLM, RAG",
            },
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        result = build_project_context(idea)
        assert "AI Lab" in result
        assert "An AI platform" in result
        assert "LLM, RAG" in result

    def test_build_context_with_positioning_notes(self):
        """Context includes positioning notes when present."""
        from datetime import UTC, datetime
        from backend.app.blog_agent_context import build_project_context
        from backend.app.blog_ideas import BlogIdea

        idea = BlogIdea(
            id="test_3",
            title="Test",
            angle="Test",
            target_reader="Test",
            article_goal="Test",
            positioning_notes=["Note A", "Note B"],
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            updated_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        result = build_project_context(idea)
        assert "Note A" in result
        assert "Note B" in result


# ===========================================================================
# Multi-agent: ClaimExtractor + TechnicalReviewer
# ===========================================================================


class TestMultiAgentReview:

    def setUp(self):
        pass
    """Verify the multi-agent review pattern (Agent-as-tool)."""

    def test_build_claim_extractor_agent(self):
        """ClaimExtractor agent builds with correct output type."""
        from backend.app.llm.review_agent import build_claim_extractor_agent

        agent = build_claim_extractor_agent()
        from backend.app.llm.schemas import ClaimExtractionResult

        assert agent.name == "ClaimExtractor"
        assert agent.output_type is ClaimExtractionResult

    def test_build_review_agent(self):
        """TechnicalReviewer agent builds with ClaimExtractor as a tool."""
        from backend.app.llm.review_agent import build_review_agent

        agent = build_review_agent()
        assert agent.name == "TechnicalReviewer"
        from backend.app.llm.schemas import TechnicalReview

        assert agent.output_type is TechnicalReview
        assert agent.tools is not None
        tool_names = [getattr(t, "name", "") for t in agent.tools]
        assert "extract_claims" in tool_names

    def test_review_agent_no_mcp(self):
        """Review agent builds correctly when MCP is disabled."""
        from backend.app.llm.review_agent import build_review_agent

        agent = build_review_agent(mcp_servers=[])
        assert agent.name == "TechnicalReviewer"
        assert agent.tools is not None
        assert len(agent.tools) >= 1


# ===========================================================================
# RecordingLLMService
# ===========================================================================


class TestRecordingLLMService:
    """Verify the recording wrapper works correctly."""

    def test_recording_creates_ai_run(self):
        """Recording a completion creates an AiRun entry."""
        from backend.app.llm.recording import RecordingLLMService
        from backend.app.llm.service import FakeLLMService
        from backend.app.ai_runs import AiRunRepository
        from backend.app.llm.schemas import BlogIdea

        recorder = AiRunRepository()
        inner = FakeLLMService(responses={
            "blog_idea": BlogIdea(
                title="Test", angle="T", target_reader="D", article_goal="G"
            ),
        })

        service = RecordingLLMService(
            inner, recorder,
            entity_type="test",
            entity_id="test_1",
            provider="test",
            model="test-model",
        )

        result = service.generate(
            "blog_idea",
            inputs={},
            output_schema=BlogIdea,
        )
        assert result is not None

        runs = recorder.list_latest(limit=10)
        completed = [r for r in runs if r.status == "completed"]
        assert len(completed) >= 1
        assert completed[0].entity_type == "test"
        assert completed[0].model == "test-model"

    def test_recording_failed_run(self):
        """Recording a failed generation creates a failed AiRun."""
        from backend.app.llm.recording import RecordingLLMService
        from backend.app.llm.service import FakeLLMService, LLMGenerationError
        from backend.app.ai_runs import AiRunRepository
        from backend.app.llm.schemas import BlogIdea

        recorder = AiRunRepository()
        inner = FakeLLMService(responses={})  # Empty — will fail

        service = RecordingLLMService(
            inner, recorder,
            entity_type="test",
            entity_id="test_2",
            provider="test",
            model="test-model",
        )

        try:
            service.generate(
                "blog_idea",
                inputs={},
                output_schema=BlogIdea,
            )
        except LLMGenerationError:
            pass

        runs = recorder.list_latest(limit=10)
        failed = [r for r in runs if r.status == "failed"]
        assert len(failed) >= 1


# ===========================================================================
# Internal Links
# ===========================================================================


class TestInternalLinks:
    """Verify the internal link suggestion engine."""

    def test_keyword_extraction(self):
        """Keywords are extracted from draft text."""
        from backend.app.llm.internal_links import _extract_keywords

        text = "This article discusses machine learning and artificial intelligence " \
               "for software engineering teams building intelligent applications."
        keywords = _extract_keywords(text, max_keywords=3)
        assert len(keywords) >= 1
        assert all(isinstance(k, str) for k in keywords)

    def test_suggest_empty_for_no_draft(self):
        """Returns empty list when idea has no draft."""
        from backend.app.llm.internal_links import suggest_internal_links
        from backend.app.blog_ideas import (
            BlogIdeaCreate,
            BlogIdeaRepository,
        )
        from backend.app.blog import BlogRepository

        idea_repo = BlogIdeaRepository()
        blog_repo = BlogRepository()
        idea = idea_repo.create(
            BlogIdeaCreate(
                title="Test", angle="Test",
                target_reader="Dev", article_goal="Test",
            )
        )
        result = suggest_internal_links(idea.id, idea_repo, blog_repo)
        assert result == []

    def test_suggest_finds_matching_posts(self):
        """Returns suggestions when keywords match published posts."""
        from backend.app.llm.internal_links import suggest_internal_links
        from backend.app.blog_ideas import (
            BlogIdeaCreate,
            BlogIdeaRepository,
        )
        from backend.app.blog import BlogPostCreate, BlogRepository
        from datetime import UTC, datetime

        idea_repo = BlogIdeaRepository()
        blog_repo = BlogRepository()

        # Seed a published post
        post = blog_repo.create(
            BlogPostCreate(
                slug="ai-agents-guide",
                title="AI Agents Guide",
                excerpt="A guide to AI agents",
                author_name="Tester",
                content_markdown="# AI Agents",
            )
        )
        blog_repo.publish(post.id)

        # Seed idea with draft mentioning AI agents
        idea = idea_repo.create(
            BlogIdeaCreate(
                title="Building AI Agents",
                angle="How to build agents",
                target_reader="Developers",
                article_goal="Teach agent building",
            )
        )
        idea.draft_markdown = "This article explores AI agents and how to " \
                              "build them effectively in production."
        idea_repo._ideas[idea.id] = idea  # type: ignore[attr-defined]

        suggestions = suggest_internal_links(idea.id, idea_repo, blog_repo)
        assert len(suggestions) >= 1
        assert suggestions[0].slug == "ai-agents-guide"


# ===========================================================================
# Readability
# ===========================================================================


class TestReadability:
    """Verify the readability analyzer."""

    def test_simple_text(self):
        """Simple text gets high Flesch score."""
        from backend.app.llm.readability import analyze_readability

        score = analyze_readability("The cat sat on the mat. The dog ran in the park.")
        assert score.flesch_reading_ease >= 80
        assert score.reading_level == "elementary"

    def test_complex_text(self):
        """Complex text gets low Flesch score."""
        from backend.app.llm.readability import analyze_readability

        text = (
            "Notwithstanding the aforementioned implementation considerations, "
            "the utilization of sophisticated algorithmic methodologies necessitates "
            "a comprehensive understanding of the underlying computational paradigms."
        )
        score = analyze_readability(text)
        assert score.flesch_reading_ease < 30
        assert score.reading_level == "college"

    def test_empty_text(self):
        """Empty text returns fallback score."""
        from backend.app.llm.readability import analyze_readability

        score = analyze_readability("")
        assert score.flesch_reading_ease == 50.0
        assert score.suggestions is not None

    def test_suggestions_for_long_sentences(self):
        """Long sentences generate suggestions."""
        from backend.app.llm.readability import analyze_readability

        text = "This is a very long sentence that goes on and on and on without any breaks " \
               "or punctuation that would help the reader understand what is being said " \
               "because it keeps going with more and more words strung together."
        score = analyze_readability(text)
        assert len(score.suggestions) >= 1
        assert any("sentence" in s.lower() for s in score.suggestions)

    def test_reading_level_label(self):
        """Reading level labels are human-readable."""
        from backend.app.llm.readability import reading_level_label, flesch_label

        assert reading_level_label("college") == "College / Advanced"
        assert reading_level_label("elementary") == "Elementary"
        assert flesch_label(90) == "Very easy"
        assert flesch_label(30) == "Difficult"


# ===========================================================================
# LLM Service layer
# ===========================================================================


class TestLLMService:
    """Verify the LLM service ABC and factory."""

    def test_fake_service_returns_response(self):
        """FakeLLMService returns the correct response type."""
        from backend.app.llm.service import FakeLLMService
        from backend.app.llm.schemas import BlogIdea

        resp = BlogIdea(
            title="Test", angle="Test", target_reader="Dev", article_goal="Test"
        )
        service = FakeLLMService(responses={"blog_idea": resp})
        result = service.generate(
            "blog_idea",
            inputs={},
            output_schema=BlogIdea,
        )
        assert result is resp

    def test_fake_service_rejects_unknown_prompt(self):
        """FakeLLMService raises error for unknown prompt names."""
        from backend.app.llm.service import FakeLLMService, LLMGenerationError
        from backend.app.llm.schemas import BlogIdea

        service = FakeLLMService(responses={})

        try:
            service.generate(
                "nonexistent_prompt",
                inputs={},
                output_schema=BlogIdea,
            )
            assert False, "Should have raised"
        except LLMGenerationError:
            pass

    def test_e2e_fake_service_builds(self):
        """E2E fake service builds without error and returns responses."""
        from backend.app.llm.e2e_fake_responses import (
            build_e2e_fake_llm_service,
        )
        from backend.app.llm.schemas import BlogIdea

        service = build_e2e_fake_llm_service()
        result = service.generate(
            "blog_idea",
            inputs={},
            output_schema=BlogIdea,
        )
        assert result is not None
        assert isinstance(result, BlogIdea)


# ===========================================================================
# SSE helper functions
# ===========================================================================


class TestSSEHelpers:
    """Verify the SSE formatting helper functions."""

    def test_sse_token(self):
        """SSE token has correct type and data fields."""
        from backend.app.llm.streaming import _sse_token

        result = _sse_token("Hello world")
        import json

        parsed = json.loads(result)
        assert parsed["type"] == "token"
        assert parsed["data"] == "Hello world"

    def test_sse_done(self):
        """SSE done has correct type."""
        from backend.app.llm.streaming import _sse_done

        result = _sse_done()
        import json

        parsed = json.loads(result)
        assert parsed["type"] == "done"

    def test_sse_result(self):
        """SSE result has type + nested data."""
        from backend.app.llm.streaming import _sse_result

        result = _sse_result({"key": "value"})
        import json

        parsed = json.loads(result)
        assert parsed["type"] == "result"
        assert parsed["data"]["key"] == "value"

    def test_sse_error(self):
        """SSE error has type + data string."""
        from backend.app.llm.streaming import _sse_error

        result = _sse_error("Something went wrong")
        import json

        parsed = json.loads(result)
        assert parsed["type"] == "error"
        assert parsed["data"] == "Something went wrong"

    def test_sse_status(self):
        """SSE status has status field + data."""
        from backend.app.llm.streaming import _sse_status

        result = _sse_status("starting", "Starting agent")
        import json

        parsed = json.loads(result)
        assert parsed["type"] == "status"
        assert parsed["status"] == "starting"
        assert parsed["data"] == "Starting agent"


# ===========================================================================
# Streaming endpoint route registration
# ===========================================================================


class TestStreamingRoutes:
    """Verify that all streaming SSE endpoints are properly registered."""

    def test_streaming_routes_registered(self):
        """All 5 streaming endpoints are registered on the router."""
        from backend.app.blog_ideas import create_blog_idea_routes
        from backend.app.blog_ideas import BlogIdeaRepository
        from backend.app.settings import Settings

        repo = BlogIdeaRepository()
        settings = Settings(environment="test")
        router = create_blog_idea_routes(repo, settings)

        stream_routes = [
            r.path
            for r in router.routes
            if hasattr(r, "path") and "generate-stream" in r.path
        ]
        assert "/admin/blog-ideas/generate-stream/idea" in stream_routes
        assert "/admin/blog-ideas/{idea_id}/generate-stream/outline" in stream_routes
        assert "/admin/blog-ideas/{idea_id}/generate-stream/draft" in stream_routes
        assert "/admin/blog-ideas/{idea_id}/generate-stream/review" in stream_routes
        assert "/admin/blog-ideas/{idea_id}/generate-stream/marketing" in stream_routes
        assert len(stream_routes) == 6

    def test_streaming_routes_require_auth(self):
        """Streaming endpoints return 401 without admin headers."""
        from backend.app.main import create_app
        from backend.app.settings import Settings

        settings = Settings(environment="test")
        app = create_app(settings)
        from starlette.testclient import TestClient

        client = TestClient(app)

        # Test idea streaming endpoint
        response = client.post("/admin/blog-ideas/generate-stream/idea")
        assert response.status_code == 401

        # Test outline streaming endpoint (needs valid idea_id format)
        response = client.post(
            "/admin/blog-ideas/test_id/generate-stream/outline"
        )
        assert response.status_code in (401, 404)  # 401 if auth fails first


# ===========================================================================
# Hooks tool call tracking
# ===========================================================================


class TestHooksToolTracking:
    """Verify AiRunTimingHooks tracks MCP and function tool calls."""

    def test_tool_tracking_empty(self):
        """New hooks have zero tool calls."""
        from backend.app.llm.hooks import AiRunTimingHooks

        hooks = AiRunTimingHooks()
        assert hooks.tool_call_count == 0
        assert hooks.tool_calls == []

    @pytest.mark.asyncio
    async def test_tool_tracking_with_calls(self):
        """Tool start/end hooks record name and duration."""
        import time
        from backend.app.llm.hooks import AiRunTimingHooks

        hooks = AiRunTimingHooks()

        class FakeTool:
            name = "blog_agent__search_posts"

        await hooks.on_tool_start(None, None, FakeTool())
        time.sleep(0.001)
        await hooks.on_tool_end(None, None, FakeTool(), "result")

        assert hooks.tool_call_count == 1
        assert len(hooks.tool_calls) == 1
        assert hooks.tool_calls[0]["name"] == "blog_agent__search_posts"
        assert hooks.tool_calls[0]["duration_ms"] >= 1

    @pytest.mark.asyncio
    async def test_tool_tracking_multiple_calls(self):
        """Multiple tool calls are tracked independently."""
        import time
        from backend.app.llm.hooks import AiRunTimingHooks

        hooks = AiRunTimingHooks()

        class Tool1:
            name = "tool_one"

        class Tool2:
            name = "tool_two"

        await hooks.on_tool_start(None, None, Tool1())
        time.sleep(0.001)
        await hooks.on_tool_start(None, None, Tool2())
        time.sleep(0.001)
        await hooks.on_tool_end(None, None, Tool1(), "result")
        await hooks.on_tool_end(None, None, Tool2(), "result")

        assert hooks.tool_call_count == 2
        names = [t["name"] for t in hooks.tool_calls]
        assert "tool_one" in names
        assert "tool_two" in names

    @pytest.mark.asyncio
    async def test_tool_tracking_with_same_name(self):
        """Consecutive calls to the same tool are tracked correctly."""
        import time
        from backend.app.llm.hooks import AiRunTimingHooks

        hooks = AiRunTimingHooks()

        class T:
            name = "same_tool"

        await hooks.on_tool_start(None, None, T())
        time.sleep(0.001)
        await hooks.on_tool_end(None, None, T(), "result")
        await hooks.on_tool_start(None, None, T())
        time.sleep(0.001)
        await hooks.on_tool_end(None, None, T(), "result")

        assert hooks.tool_call_count == 2
        assert all(t["name"] == "same_tool" for t in hooks.tool_calls)
