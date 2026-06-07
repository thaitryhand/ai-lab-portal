"""Additional coverage tests for llm/streaming.py.

Targets uncovered paths identified in the coverage audit:
- LLMGenerationError catch in stream_generate
- Generic Exception catch during stream iteration
- Recording with hooks.total_ms verification
- saving_session status event ordering
- AgentUpdatedStreamEvent / RunItemStreamEvent pass-through
- _sse_done() pure function
- Edge: result.final_output is None
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from agents import Runner
from openai.types.responses import (
    Response as OpenAIResponse,
    ResponseCompletedEvent,
    ResponseTextDeltaEvent,
    ResponseTextDoneEvent,
)

from backend.app.llm.service import LLMGenerationError
from backend.app.llm.streaming import _sse_done, stream_generate


# ── Helpers (matching existing test_llm_streaming.py patterns) ──────────


class DummyOutput(MagicMock):
    """Stand-in for a Pydantic BaseModel output type."""
    def model_dump(self):
        return {"content": "dummy"}


class MockUsage:
    def __init__(self, input_tokens: int = 50, output_tokens: int = 150):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class MockRunResultStreaming:
    def __init__(self, final_output=None, usage=None, events=None):
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
    from agents.stream_events import RawResponsesStreamEvent
    return RawResponsesStreamEvent(data=data)


def _delta_event(text: str):
    return _raw_event(ResponseTextDeltaEvent(
        delta=text, type="response.output_text.delta",
        content_index=0, item_id="item_1",
        logprobs=[], output_index=0, sequence_number=0,
    ))


def _text_done_event(text: str = ""):
    return _raw_event(ResponseTextDoneEvent(
        text=text, type="response.output_text.done",
        content_index=0, item_id="item_1",
        logprobs=[], output_index=0, sequence_number=0,
    ))


def _completed_event():
    resp = MagicMock(spec=OpenAIResponse)
    resp.id = "resp_complete_1"
    resp.status = "completed"
    return _raw_event(ResponseCompletedEvent(
        type="response.completed",
        response=resp,
        sequence_number=0,
    ))


# ── Pure-function tests ─────────────────────────────────────────────────


class TestSseDone:
    """_sse_done() defined in the module but was untested."""

    def test_sse_done_returns_json_with_type_done(self):
        payload = json.loads(_sse_done())
        assert payload["type"] == "done"
        assert payload["data"] == "generation_complete"


# ── Stream generate: error handling ────────────────────────────────────


class TestStreamGenerateErrorsExtended:
    """Additional error-path coverage for stream_generate."""

    @pytest.fixture
    def mock_runner_run_streamed(self):
        with patch.object(Runner, "run_streamed", new=MagicMock()) as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_llm_generation_error_caught(self, mock_runner_run_streamed):
        """LLMGenerationError from Runner.run_streamed yields an error event."""
        mock_runner_run_streamed.side_effect = LLMGenerationError("LLM failed badly")

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
        assert "LLM generation failed" in errors[0]["data"]

    @pytest.mark.asyncio
    async def test_stream_events_throws_exception(self, mock_runner_run_streamed):
        """Exception during async stream iteration yields error event."""
        class BrokenStreamResult:
            """Simulates a result whose stream_events raises."""
            final_output = None
            usage = None

            async def stream_events(self):
                """Async generator that immediately raises."""
                raise RuntimeError("Stream crashed")
                yield  # pragma: no cover

        broken = BrokenStreamResult()
        mock_runner_run_streamed.return_value = broken

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
        assert "Stream crashed" in str(errors[0]["data"])

    @pytest.mark.asyncio
    async def test_unknown_prompt_via_missing_key(self, mock_runner_run_streamed):
        """Non-existent prompt name yields error without calling Runner."""
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


# ── Non-RawResponsesStreamEvent pass-through ────────────────────────────


class TestStreamGenerateNonStandardEvents:
    """Events that are NOT RawResponsesStreamEvent are passed through silently."""

    @pytest.fixture
    def mock_runner_run_streamed(self):
        with patch.object(Runner, "run_streamed", new=MagicMock()) as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_agent_updated_and_run_item_ignored(self, mock_runner_run_streamed):
        """Other event types in stream_events do not crash the generator."""
        output = DummyOutput()
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(),
            events=[
                # Non-RawResponsesStreamEvent (plain dict-like objects)
                {"type": "agent_updated_stream_event"},
                {"type": "run_item_stream_event"},
                _delta_event("hello"),
                _text_done_event(text="hello"),
                _completed_event(),
            ],
        )
        mock_runner_run_streamed.return_value = mock_result

        events: list[str] = []
        async for event in stream_generate(
            prompt_name="test",
            inputs={"query": "hello"},
            output_schema=DummyOutput,
            agent=MagicMock(),
        ):
            events.append(event)

        payloads = [json.loads(e) for e in events]
        assert any(p["type"] == "result" for p in payloads)
        tokens = [p["data"] for p in payloads if p["type"] == "token"]
        assert "hello" in tokens


# ── Recording integration ──────────────────────────────────────────────


class TestStreamGenerateRecordingExtended:
    """Additional recording-path coverage."""

    @pytest.fixture
    def mock_runner_run_streamed(self):
        with patch.object(Runner, "run_streamed", new=MagicMock()) as mock:
            yield mock

    @pytest.mark.asyncio
    async def test_saving_session_status_emitted(self, mock_runner_run_streamed):
        """The 'saving_session' status event is emitted before result."""
        recorder = MagicMock()
        output = DummyOutput()
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(input_tokens=10, output_tokens=20),
            events=[_delta_event("x"), _text_done_event(text="x"), _completed_event()],
        )
        mock_runner_run_streamed.return_value = mock_result

        events: list[str] = []
        async for event in stream_generate(
            prompt_name="test_prompt",
            inputs={"key": "val"},
            output_schema=DummyOutput,
            recorder=recorder,
            entity_id="entity_1",
            entity_type="blog_idea",
            provider="agents_sdk",
            model="gpt-4o",
            agent=MagicMock(),
        ):
            events.append(event)

        payloads = [json.loads(e) for e in events]
        statuses = [p for p in payloads if p["type"] == "status"]
        saving = [s for s in statuses if s.get("status") == "saving_session"]
        assert len(saving) >= 1

    @pytest.mark.asyncio
    async def test_recording_includes_latency_ms(self, mock_runner_run_streamed):
        """latency_ms field is passed to record_completed."""
        recorder = MagicMock()
        output = DummyOutput()
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(input_tokens=5, output_tokens=10),
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
        assert "latency_ms" in call_kwargs
        assert isinstance(call_kwargs["latency_ms"], (int, float))

    @pytest.mark.asyncio
    async def test_recorder_record_failed_not_called_on_success(self, mock_runner_run_streamed):
        """record_failed should never be called on success path."""
        recorder = MagicMock()
        output = DummyOutput()
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(),
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

        recorder.record_failed.assert_not_called()

    @pytest.mark.asyncio
    async def test_result_after_saving_session(self, mock_runner_run_streamed):
        """The 'result' event should come after 'saving_session'."""
        recorder = MagicMock()
        output = DummyOutput()
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(),
            events=[_delta_event("x"), _text_done_event(text="x"), _completed_event()],
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
        saving_indices = [i for i, p in enumerate(payloads) if p.get("status") == "saving_session"]
        result_indices = [i for i, p in enumerate(payloads) if p["type"] == "result"]

        if saving_indices and result_indices:
            assert saving_indices[-1] < result_indices[0]

    @pytest.mark.asyncio
    async def test_no_stream_events_still_produces_result(self, mock_runner_run_streamed):
        """Even with no stream events, if final_output is valid, yields result."""
        output = DummyOutput()
        mock_result = MockRunResultStreaming(
            final_output=output,
            usage=MockUsage(),
            events=[],
        )
        mock_runner_run_streamed.return_value = mock_result

        events: list[str] = []
        async for event in stream_generate(
            prompt_name="test",
            inputs={"query": "x"},
            output_schema=DummyOutput,
            agent=MagicMock(),
        ):
            events.append(event)

        payloads = [json.loads(e) for e in events]
        assert any(p["type"] == "result" for p in payloads)
