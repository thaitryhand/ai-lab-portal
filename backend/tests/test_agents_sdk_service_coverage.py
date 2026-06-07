"""Additional coverage tests for llm/agents_sdk_service.py.

Targets edge cases uncovered by existing test_agents_sdk_service.py:
- Recorder record_failed path when LLMGenerationError wraps non-Exception types
- recorder not called when entity_id is None but recorder is provided (failure path)
- recorder not called without recorder (failure path)
- Guardrails: empty list vs None distinction on Agent
- Max_tokens for draft_section_writer with 16000 tokens
- Agent construction with empty mcp_servers
- Session save on failure path (should NOT be called)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, Field

from backend.app.llm.agents_sdk_service import AgentsSDKLLMService


# ── Helpers ──────────────────────────────────────────────────────────────


class _DummyOutput(BaseModel):
    content: str = Field(default="ok")
    score: int = Field(default=0)


def _make_mock_result(
    final_output: BaseModel | None = None,
    *,
    has_usage: bool = True,
    input_tokens: int = 50,
    output_tokens: int = 100,
    state=None,
) -> MagicMock:
    result = MagicMock()
    result.final_output = final_output or _DummyOutput(content="ok", score=1)
    if has_usage:
        usage = MagicMock()
        usage.input_tokens = input_tokens
        usage.output_tokens = output_tokens
        result.usage = usage
    else:
        result.usage = None
    result.to_state.return_value = state or MagicMock()
    return result


# ── Recorder failure paths ──────────────────────────────────────────────


class TestRecorderFailurePaths:
    """Edge cases for recording on failure."""

    def test_record_failed_when_entity_id_none_and_recorder_provided(self):
        """When entity_id is None but recorder is provided, failure should NOT call record_failed."""
        recorder = MagicMock()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            side_effect=ValueError("fail"),
        ):
            service = AgentsSDKLLMService(
                api_key="test-key",
                recorder=recorder,
                # entity_id is intentionally None
            )
            with pytest.raises(Exception):
                service.generate_with_usage("blog_idea", {
                    "project_name": "Test", "project_summary": "Test",
                    "ai_capabilities": "LLM", "technical_highlights": "None",
                    "business_value": "Value",
                }, _DummyOutput)

        recorder.record_failed.assert_not_called()

    def test_record_failed_not_called_without_recorder(self):
        """When no recorder is provided, failure does not call record_failed."""
        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            side_effect=ValueError("fail"),
        ):
            service = AgentsSDKLLMService(
                api_key="test-key",
                entity_id="idea-1",
                # recorder is intentionally None
            )
            with pytest.raises(Exception):
                service.generate_with_usage("blog_idea", {
                    "project_name": "Test", "project_summary": "Test",
                    "ai_capabilities": "LLM", "technical_highlights": "None",
                    "business_value": "Value",
                }, _DummyOutput)

    def test_record_completed_not_called_without_entity_id(self):
        """When entity_id is None but recorder is provided, success should NOT call record_completed."""
        recorder = MagicMock()
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(
                api_key="test-key",
                recorder=recorder,
                # entity_id is intentionally None
            )
            service.generate_with_usage("blog_idea", {
                "project_name": "Test", "project_summary": "Test",
                "ai_capabilities": "LLM", "technical_highlights": "None",
                "business_value": "Value",
            }, _DummyOutput)

        recorder.record_completed.assert_not_called()

    def test_record_completed_not_called_without_recorder(self):
        """When no recorder is provided, success does not call record_completed."""
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(
                api_key="test-key",
                entity_id="idea-1",
                # recorder is intentionally None
            )
            service.generate_with_usage("blog_idea", {
                "project_name": "Test", "project_summary": "Test",
                "ai_capabilities": "LLM", "technical_highlights": "None",
                "business_value": "Value",
            }, _DummyOutput)


# ── Session store edge cases ──────────────────────────────────────────


class TestSessionStoreEdgeCases:
    """Edge cases for session store operations."""

    def test_session_store_not_called_on_failure(self):
        """When Runner.run_sync raises, session_store.save should NOT be called."""
        session_store = MagicMock()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            side_effect=ValueError("fail"),
        ):
            service = AgentsSDKLLMService(
                api_key="test-key",
                session_store=session_store,
                entity_id="idea-1",
            )
            with pytest.raises(Exception):
                service.generate_with_usage("blog_idea", {
                    "project_name": "Test", "project_summary": "Test",
                    "ai_capabilities": "LLM", "technical_highlights": "None",
                    "business_value": "Value",
                }, _DummyOutput)

        session_store.save.assert_not_called()

    def test_session_store_to_state_not_called_without_store(self):
        """Without session_store, to_state should not be called."""
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ):
            service = AgentsSDKLLMService(
                api_key="test-key",
                entity_id="idea-1",
            )
            service.generate_with_usage("blog_idea", {
                "project_name": "Test", "project_summary": "Test",
                "ai_capabilities": "LLM", "technical_highlights": "None",
                "business_value": "Value",
            }, _DummyOutput)

        mock_result.to_state.assert_not_called()


# ── Guardrails edge cases ──────────────────────────────────────────────


class TestGuardrailsEdgeCases:
    """Edge cases for guardrail registration and usage."""

    def test_agent_gets_empty_list_not_none_for_guardrails(self):
        """When no guardrails registered, Agent.output_guardrails should be empty list."""
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ) as mock_run:
            service = AgentsSDKLLMService(api_key="test-key")
            service.generate_with_usage("blog_idea", {
                "project_name": "Test", "project_summary": "Test",
                "ai_capabilities": "LLM", "technical_highlights": "None",
                "business_value": "Value",
            }, _DummyOutput)

        agent = mock_run.call_args[0][0]
        assert agent.output_guardrails == []


# ── Max tokens ─────────────────────────────────────────────────────────


class TestMaxTokensExtended:
    """Additional max_tokens edge cases."""

    def test_draft_writer_with_custom_model_passes_max_tokens(self):
        """Max_tokens=16000 passed for draft_writer even with custom model."""
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ) as mock_run:
            service = AgentsSDKLLMService(api_key="test-key", model="o3-mini")
            service.generate_with_usage("draft_writer", {
                "outline_json": "{}", "project_context": "test",
                "positioning_notes": "",
            }, _DummyOutput)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("max_tokens") == 16000

    def test_draft_section_writer_passes_max_tokens(self):
        """Max_tokens=16000 passed for draft_section_writer."""
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ) as mock_run:
            service = AgentsSDKLLMService(api_key="test-key")
            service.generate_with_usage("draft_section_writer", {
                "outline_json": "{}", "project_context": "test",
                "positioning_notes": "", "section_index": "1",
                "section_total": "5", "section_heading": "Intro",
                "section_points": "point", "prior_sections_summary": "none",
            }, _DummyOutput)

        call_kwargs = mock_run.call_args[1]
        assert call_kwargs.get("max_tokens") == 16000

    def test_technical_review_does_not_pass_max_tokens(self):
        """Technical review prompt does not get max_tokens override."""
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ) as mock_run:
            service = AgentsSDKLLMService(api_key="test-key")
            service.generate_with_usage("technical_review", {
                "draft_markdown": "# Draft", "project_context": "test",
            }, _DummyOutput)

        call_kwargs = mock_run.call_args[1]
        assert "max_tokens" not in call_kwargs


# ── Agent construction ──────────────────────────────────────────────────


class TestAgentConstruction:
    """Edge cases in agent construction from prompts."""

    def test_mcp_servers_empty_list(self):
        """Empty mcp_servers list is passed to Agent correctly."""
        mock_result = _make_mock_result()

        with patch(
            "backend.app.llm.agents_sdk_service.Runner.run_sync",
            return_value=mock_result,
        ) as mock_run:
            service = AgentsSDKLLMService(
                api_key="test-key",
                mcp_servers=[],
            )
            service.generate_with_usage("blog_idea", {
                "project_name": "Test", "project_summary": "Test",
                "ai_capabilities": "LLM", "technical_highlights": "None",
                "business_value": "Value",
            }, _DummyOutput)

        agent = mock_run.call_args[0][0]
        assert agent.mcp_servers == []


# ── Tracing disabled ────────────────────────────────────────────────────


class TestTracingDisabled:
    """set_tracing_disabled helper."""

    def test_set_tracing_disabled_importable(self):
        """The set_tracing_disabled function is importable and callable."""
        from backend.app.llm.agents_sdk_service import set_tracing_disabled
        # Just verify it doesn't raise
        set_tracing_disabled(True)
        set_tracing_disabled(False)
