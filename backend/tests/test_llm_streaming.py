"""Tests for llm/streaming.py — SSE streaming generator and formatters.

Tests the synchronous SSE helpers and the async ``stream_generate()``
generator with mocked ``Runner.run_streamed()``.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agents import Runner
from agents.stream_events import RawResponsesStreamEvent
from openai.types.responses import (
    Response as OpenAIResponse,
    ResponseCompletedEvent,
    ResponseErrorEvent,
    ResponseFailedEvent,
    ResponseTextDeltaEvent,
    ResponseTextDoneEvent,
)
from pydantic import BaseModel

from backend.app.llm.schemas import BlogIdea
from backend.app.llm.streaming import (
    _sse_done,
    _sse_error,
    _sse_result,
    _sse_status,
    _sse_token,
    stream_generate,
)


# ─── Test models ────────────────────────────────────────────────────────


class DummyOutput(BaseModel):
    content: str = "hello"


# ─── SSE Formatting Helpers ─────────────────────────────────────────────


class TestSseFormatters:
    """Pure-function tests for SSE helpers — no mocks needed."""

    def test_sse_token_returns_json_with_type_token(self):
        payload = json.loads(_sse_token("Hello"))
        assert payload["type"] == "token"
        assert payload["data"] == "Hello"

    def test_sse_token_handles_multi_word(self):
        payload = json.loads(_sse_token("Hello world"))
        assert payload["data"] == "Hello world"

    def test_sse_done_returns_json_with_type_done(self):
        payload = json.loads(_sse_done())
        assert payload["type"] == "done"
        assert payload["data"] == "generation_complete"

    def test_sse_result_returns_json_with_result_data(self):
        payload = json.loads(_sse_result({"key": "value"}))
        assert payload["type"] == "result"
        assert payload["data"]["key"] == "value"

    def test_sse_error_returns_json_with_error_type(self):
        payload = json.loads(_sse_error("Something went wrong"))
        assert payload["type"] == "error"
        assert "Something went wrong" in payload["data"]

    def test_sse_status_returns_json_with_status_type(self):
        payload = json.loads(_sse_status("starting", "Agent started"))
        assert payload["type"] == "status"
        assert payload["status"] == "starting"
        assert payload["data"] == "Agent started"


# ─── Stream Generate (mocked Runner) ────────────────────────────────────


class MockUsage:
    """Simulates ``RunResultStreaming.usage``."""

    def __init__(self, input_tokens: int = 50, output_tokens: int = 150):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class MockRunResultStreaming:
    """Simulates the object returned by ``Runner.run_streamed()``."""

    def __init__(self, final_output, usage: MockUsage | None = None, events: list | None = None):
        self.final_output = final_output
        self._usage = usage
        self._events = events or []

    @property
    def usage(self):
        return self._usage

    async def stream_events(self):
        for event in self._events:
            yield event


def _raw_event(data):
    """Convenience: wrap an OpenAI response data in RawResponsesStreamEvent."""
    return RawResponsesStreamEvent(data=data)


def _delta_event(text: str):
    return _raw_event(ResponseTextDeltaEvent(
        delta=text,
        type="response.output_text.delta",
        content_index=0,
        item_id="item_1",
        logprobs=[],
        output_index=0,
        sequence_number=0,
    ))


def _text_done_event(text: str = ""):
    return _raw_event(ResponseTextDoneEvent(
        text=text,
        type="response.output_text.done",
        content_index=0,
        item_id="item_1",
        logprobs=[],
        output_index=0,
        sequence_number=0,
    ))


def _completed_event():
    resp = MagicMock(spec=OpenAIResponse)
    resp.id = "resp_complete_1"
    resp.status = "completed"
    return _raw_event(ResponseCompletedEvent(
        type="response.completed",
        response=resp,  # type: ignore[arg-type]
        sequence_number=0,
    ))


def _error_event(code: str = "ERROR", message: str = "Test error"):
    return _raw_event(ResponseErrorEvent(
        code=code,
        message=message,
        param=None,
        type="error",
        sequence_number=0,
    ))


def _failed_event(code: str = "FAIL", message: str = "Test failure"):
    resp = MagicMock(spec=OpenAIResponse)
    resp.id = "resp_fail_1"
    resp.status = "failed"
    return _raw_event(ResponseFailedEvent(
        code=code,
        message=message,
        type="response.failed",
        response=resp,  # type: ignore[arg-type]
        sequence_number=0,
    ))


@pytest.fixture
def mock_runner_run_streamed():
    """Patch Runner.run_streamed to return a controllable mock."""
    with patch.object(Runner, "run_streamed", new=AsyncMock()) as mock:
        yield mock


# ─── Tests ──────────────────────────────────────────────────────────────


class TestStreamGenerateBasic:
    """Happy path: successful streaming with mock agent."""

    @pytest.mark.asyncio
    async def test_uses_prebuilt_agent(self, mock_runner_run_streamed):
        """When an Agent is passed, prompt_name/output_schema are bypassed."""
        output = DummyOutput(content="streamed_result")
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(input_tokens=50, output_tokens=100),
            events=[
                _delta_event("Hello"),
                _delta_event(" world"),
                _text_done_event(text="Hello world"),
                _completed_event(),
            ],
        )
        mock_runner_run_streamed.return_value = mock_result

        from agents import Agent

        agent = Agent(name="test_agent", instructions="Test", output_type=DummyOutput)
        events: list[str] = []
        async for event in stream_generate(
            prompt_name="ignored",
            inputs={"query": "test"},
            output_schema=DummyOutput,
            agent=agent,
        ):
            events.append(event)

        # Should yield token events, then status, then result
        payloads = [json.loads(e) for e in events]
        types = [p["type"] for p in payloads]

        assert "token" in types, "Should yield at least one token event"
        assert "result" in types, "Should yield a final result event"
        # Verify token deltas
        token_data = [p["data"] for p in payloads if p["type"] == "token"]
        assert "".join(token_data) == "Hello world"

    @pytest.mark.asyncio
    async def test_yields_tokens_in_order(self, mock_runner_run_streamed):
        """Token deltas arrive in the correct order."""
        output = DummyOutput(content="hello")
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(),
            events=[
                _delta_event("First"),
                _delta_event(" "),
                _delta_event("Second"),
                _text_done_event(text="First Second"),
                _completed_event(),
            ],
        )
        mock_runner_run_streamed.return_value = mock_result

        tokens: list[str] = []
        async for event in stream_generate(
            prompt_name="test",
            inputs={"query": "hello"},
            output_schema=DummyOutput,
            agent=MagicMock(spec=["run"]),
        ):
            payload = json.loads(event)
            if payload["type"] == "token":
                tokens.append(payload["data"])

        assert tokens == ["First", " ", "Second"]

    @pytest.mark.asyncio
    async def test_yields_result_with_output(self, mock_runner_run_streamed):
        """Final output is yielded as a 'result' event with dumped data."""
        output = DummyOutput(content="final_output")
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(),
            events=[_delta_event("x"), _text_done_event(text="x"), _completed_event()],
        )
        mock_runner_run_streamed.return_value = mock_result

        async for event in stream_generate(
            prompt_name="test",
            inputs={"query": "x"},
            output_schema=DummyOutput,
            agent=MagicMock(spec=["run"]),
        ):
            payload = json.loads(event)
            if payload["type"] == "result":
                assert payload["data"]["content"] == "final_output"


class TestStreamGenerateErrors:
    """Error and edge-case paths."""

    @pytest.mark.asyncio
    async def test_unknown_prompt_returns_immediate_error(self, mock_runner_run_streamed):
        """When prompt_name is not in the registry, yield an error and stop."""
        events: list[str] = []
        async for event in stream_generate(
            prompt_name="nonexistent_prompt_xyz",
            inputs={},
            output_schema=DummyOutput,
        ):
            events.append(event)

        assert len(events) == 1, "Should yield exactly one error event"
        payload = json.loads(events[0])
        assert payload["type"] == "error"
        assert "nonexistent_prompt_xyz" in payload["data"]
        # Runner.run_streamed should not have been called
        mock_runner_run_streamed.assert_not_called()

    @pytest.mark.asyncio
    async def test_response_error_event(self, mock_runner_run_streamed):
        """ResponseErrorEvent from the stream stops generation gracefully."""
        output = DummyOutput(content="partial")
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(),
            events=[_delta_event("partial"), _error_event(code="RATE_LIMIT", message="Rate limited")],
        )
        mock_runner_run_streamed.return_value = mock_result

        events: list[str] = []
        async for event in stream_generate(
            prompt_name="test", inputs={"query": "x"}, output_schema=DummyOutput, agent=MagicMock()
        ):
            events.append(event)

        payloads = [json.loads(e) for e in events]
        errors = [p for p in payloads if p["type"] == "error"]
        assert len(errors) > 0
        assert "RATE_LIMIT" in errors[0]["data"]

    @pytest.mark.asyncio
    async def test_response_failed_event(self, mock_runner_run_streamed):
        """ResponseFailedEvent stops generation gracefully."""
        output = DummyOutput(content="")
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(),
            events=[_failed_event(code="CONTENT_FILTER", message="Blocked")],
        )
        mock_runner_run_streamed.return_value = mock_result

        events: list[str] = []
        async for event in stream_generate(
            prompt_name="test", inputs={"query": "x"}, output_schema=DummyOutput, agent=MagicMock()
        ):
            events.append(event)

        payloads = [json.loads(e) for e in events]
        errors = [p for p in payloads if p["type"] == "error"]
        assert len(errors) > 0
        assert "CONTENT_FILTER" in errors[0]["data"]

    @pytest.mark.asyncio
    async def test_wrong_output_type_yields_error(self, mock_runner_run_streamed):
        """If final_output is not an instance of output_schema, yield error."""
        mock_result = MockRunResultStreaming(
            final_output="not_a_model",  # string, not DummyOutput
            usage=MockUsage(),
            events=[_delta_event("x"), _text_done_event(text="x"), _completed_event()],
        )
        mock_runner_run_streamed.return_value = mock_result

        events: list[str] = []
        async for event in stream_generate(
            prompt_name="test", inputs={"query": "x"}, output_schema=DummyOutput, agent=MagicMock()
        ):
            events.append(event)

        payloads = [json.loads(e) for e in events]
        errors = [p for p in payloads if p["type"] == "error"]
        assert len(errors) >= 1
        assert any("DummyOutput" in e["data"] for e in errors)

    @pytest.mark.asyncio
    async def test_general_exception_returns_error(self, mock_runner_run_streamed):
        """Unexpected exceptions are caught and yield as error events."""
        mock_runner_run_streamed.side_effect = RuntimeError("Unexpected crash")

        events: list[str] = []
        async for event in stream_generate(
            prompt_name="test",
            inputs={"query": "x"},
            output_schema=DummyOutput,
            agent=MagicMock(),
        ):
            events.append(event)

        payloads = [json.loads(e) for e in events]
        errors = [p for p in payloads if p["type"] == "error"]
        assert len(errors) >= 1
        assert "Unexpected crash" in errors[0]["data"]

    @pytest.mark.asyncio
    async def test_empty_inputs_with_agent(self, mock_runner_run_streamed):
        """When agent is provided but inputs is empty, it should still work."""
        output = DummyOutput(content="done")
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(),
            events=[_delta_event("done"), _text_done_event(text="done"), _completed_event()],
        )
        mock_runner_run_streamed.return_value = mock_result

        events: list[str] = []
        async for event in stream_generate(
            prompt_name="test",
            inputs={},
            output_schema=DummyOutput,
            agent=MagicMock(),
        ):
            events.append(event)

        payloads = [json.loads(e) for e in events]
        assert any(p["type"] == "result" for p in payloads)


class TestStreamGenerateRecording:
    """Recording (AiRunRepository) integration in streaming path."""

    @pytest.mark.asyncio
    async def test_recording_called_when_recorder_provided(self, mock_runner_run_streamed):
        """When recorder + entity_id are provided, record_completed is called."""
        recorder = MagicMock()
        output = DummyOutput(content="recorded")
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(input_tokens=20, output_tokens=80),
            events=[_delta_event("r"), _text_done_event(text="r"), _completed_event()],
        )
        mock_runner_run_streamed.return_value = mock_result

        async for _ in stream_generate(
            prompt_name="test_prompt",
            inputs={"key": "val"},
            output_schema=DummyOutput,
            recorder=recorder,
            entity_id="entity_123",
            entity_type="blog_idea",
            provider="agents_sdk",
            model="gpt-4o",
            agent=MagicMock(),
        ):
            pass

        recorder.record_completed.assert_called_once()
        call_kwargs = recorder.record_completed.call_args[1]
        assert call_kwargs["prompt_name"] == "test_prompt"
        assert call_kwargs["entity_id"] == "entity_123"
        assert call_kwargs["entity_type"] == "blog_idea"
        assert call_kwargs["provider"] == "agents_sdk"
        assert call_kwargs["model"] == "gpt-4o"
        assert call_kwargs["input_payload"] == {"key": "val"}
        assert call_kwargs["output_payload"] == {"content": "recorded"}
        assert call_kwargs["prompt_tokens"] == 20
        assert call_kwargs["completion_tokens"] == 80
        assert call_kwargs["total_tokens"] == 100

    @pytest.mark.asyncio
    async def test_recording_skipped_without_entity_id(self, mock_runner_run_streamed):
        """If entity_id is None, recording is skipped."""
        recorder = MagicMock()
        output = DummyOutput(content="skipped")
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(),
            events=[_delta_event("s"), _text_done_event(text="s"), _completed_event()],
        )
        mock_runner_run_streamed.return_value = mock_result

        async for _ in stream_generate(
            prompt_name="test",
            inputs={"k": "v"},
            output_schema=DummyOutput,
            recorder=recorder,  # provided but entity_id is None
            agent=MagicMock(),
        ):
            pass

        recorder.record_completed.assert_not_called()

    @pytest.mark.asyncio
    async def test_recording_failure_yields_warning(self, mock_runner_run_streamed):
        """Recording exceptions are non-fatal and yield a status warning."""
        recorder = MagicMock()
        recorder.record_completed.side_effect = ValueError("DB conn lost")
        output = DummyOutput(content="warning")
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(),
            events=[_delta_event("w"), _text_done_event(text="w"), _completed_event()],
        )
        mock_runner_run_streamed.return_value = mock_result

        events: list[str] = []
        async for event in stream_generate(
            prompt_name="test",
            inputs={"k": "v"},
            output_schema=DummyOutput,
            recorder=recorder,
            entity_id="e1",
            entity_type="blog_idea",
            provider="agents_sdk",
            agent=MagicMock(),
        ):
            events.append(event)

        payloads = [json.loads(e) for e in events]
        statuses = [p for p in payloads if p["type"] == "status"]
        record_warnings = [s for s in statuses if s.get("status") == "record_warning"]
        assert len(record_warnings) >= 1
        assert "DB conn lost" in record_warnings[0]["data"]

    @pytest.mark.asyncio
    async def test_no_usage_yields_none_tokens(self, mock_runner_run_streamed):
        """When usage is None, token fields should be None in recording."""
        recorder = MagicMock()
        output = DummyOutput(content="no_usage")
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=None,  # No usage info
            events=[_delta_event("x"), _text_done_event(text="x"), _completed_event()],
        )
        mock_runner_run_streamed.return_value = mock_result

        async for _ in stream_generate(
            prompt_name="test",
            inputs={"k": "v"},
            output_schema=DummyOutput,
            recorder=recorder,
            entity_id="e1",
            entity_type="blog_idea",
            provider="agents_sdk",
            agent=MagicMock(),
        ):
            pass

        call_kwargs = recorder.record_completed.call_args[1]
        assert call_kwargs["prompt_tokens"] is None
        assert call_kwargs["completion_tokens"] is None
        assert call_kwargs["total_tokens"] is None


class TestStreamGenerateWithRealAgent:
    """Tests that exercise the agent construction path (prompt registry)."""

    @pytest.mark.asyncio
    async def test_builds_agent_from_registry(self, mock_runner_run_streamed):
        """Without a pre-built agent, the generator builds one from the prompt registry."""
        output = BlogIdea(
            title="Test Idea",
            angle="AI",
            target_reader="Devs",
            article_goal="Test",
        )
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(),
            events=[_delta_event("x"), _text_done_event(text="x"), _completed_event()],
        )
        mock_runner_run_streamed.return_value = mock_result

        async for event in stream_generate(
            prompt_name="blog_idea",
            inputs={
                "project_name": "Test",
                "project_summary": "A test",
                "ai_capabilities": "LLM",
                "technical_highlights": "Structured output",
                "business_value": "Efficiency",
            },
            output_schema=BlogIdea,
        ):
            pass

        # Runner.run_streamed should have been called
        mock_runner_run_streamed.assert_awaited_once()
        call_args = mock_runner_run_streamed.call_args
        agent_arg = call_args[0][0]  # first positional: starting_agent
        assert agent_arg is not None
        assert agent_arg.name == "blog_idea"

    @pytest.mark.asyncio
    async def test_unknown_prompt_without_agent_returns_error(self, mock_runner_run_streamed):
        """Missing prompt name yields an error without calling Runner."""
        events: list[str] = []
        async for event in stream_generate(
            prompt_name="__does_not_exist__",
            inputs={},
            output_schema=DummyOutput,
        ):
            events.append(event)

        assert len(events) == 1
        assert "__does_not_exist__" in json.loads(events[0])["data"]
        mock_runner_run_streamed.assert_not_called()
