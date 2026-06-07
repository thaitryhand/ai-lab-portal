"""AgentHooks and RunHooks for the Agents SDK LLM service.

Replaces the ``RecordingLLMService`` wrapper pattern with native SDK lifecycle
hooks that integrate directly with the agent execution pipeline.

Key hooks:
- ``AiRunTimingHooks`` — Tracks per-agent and per-LLM-call timing data.
  The ``AgentsSDKLLMService`` reads timing from these hooks after
  ``Runner.run_sync()`` returns and combines it with result data (usage,
  output) for recording to ``AiRunRepository``.
- Future hooks can extend this for tool-call tracking, handoff monitoring,
  or real-time logging.
"""

from __future__ import annotations

import time
from typing import Any

from agents import RunHooks
from agents.run_context import AgentHookContext


class AiRunTimingHooks(RunHooks):
    """Tracks agent run timing via RunHooks lifecycle.

    Records per-agent start/end times and per-LLM-call timing data.
    The calling service reads this data after ``Runner.run_sync()``
    returns and combines it with result metadata for persistence.

    Also tracks MCP / function tool calls so that downstream recording
    can attribute latency to tool usage.

    Usage::

        hooks = AiRunTimingHooks()
        result = Runner.run_sync(agent, input, hooks=hooks)

        latency_ms = hooks.total_ms
        llm_count = hooks.llm_call_count
        tool_calls = hooks.tool_calls  # list of dicts
    """

    def __init__(self) -> None:
        self._agent_start: float = 0.0
        self._agent_end: float = 0.0
        self._llm_starts: list[float] = []
        self._llm_ends: list[float] = []
        # Tool call tracking
        self._tool_starts: dict[int, dict[str, Any]] = {}
        self._tool_results: list[dict[str, Any]] = []
        self._tool_counter: int = 0

    # ── Agent lifecycle ────────────────────────────────────────────────

    async def on_agent_start(self, context: AgentHookContext[Any], agent: Any) -> None:
        """Capture the moment an agent begins execution."""
        self._agent_start = time.perf_counter()

    async def on_agent_end(
        self, context: AgentHookContext[Any], agent: Any, output: Any
    ) -> None:
        """Capture the moment an agent finishes execution."""
        self._agent_end = time.perf_counter()

    # ── LLM call lifecycle ─────────────────────────────────────────────

    async def on_llm_start(
        self,
        context: Any,
        agent: Any,
        system_prompt: str | None,
        input_items: list[Any],
    ) -> None:
        """Capture the start of each LLM call within an agent run."""
        self._llm_starts.append(time.perf_counter())

    async def on_llm_end(
        self, context: Any, agent: Any, response: Any
    ) -> None:
        """Capture the end of each LLM call within an agent run."""
        self._llm_ends.append(time.perf_counter())

    # ── Tool call lifecycle (MCP tools, function tools, etc.) ──────────

    def _tool_name(self, tool: Any) -> str:
        """Extract a human-readable name from any tool type."""
        raw = (
            getattr(tool, "name", None)
            or getattr(tool, "qualified_name", None)
            or str(tool)
        )
        return str(raw)

    async def on_tool_start(
        self,
        context: AgentHookContext[Any],
        agent: Any,
        tool: Any,
    ) -> None:
        """Capture the start of a tool call (MCP, function tool, etc.)."""
        idx = self._tool_counter
        self._tool_counter += 1
        self._tool_starts[idx] = {
            "name": self._tool_name(tool),
            "start": time.perf_counter(),
        }

    async def on_tool_end(
        self,
        context: AgentHookContext[Any],
        agent: Any,
        tool: Any,
        result: Any,
    ) -> None:
        """Capture the end of a tool call and record its timing."""
        name = self._tool_name(tool)
        now = time.perf_counter()
        # Match by name (reverse-order to handle parallel calls gracefully)
        for idx in reversed(range(self._tool_counter)):
            entry = self._tool_starts.get(idx)
            if entry is not None and entry["name"] == name and "end" not in entry:
                entry["end"] = now
                entry["duration_ms"] = int((now - entry["start"]) * 1000)
                self._tool_results.append(entry)
                break

    # ── Computed properties ────────────────────────────────────────────

    @property
    def total_ms(self) -> int:
        """Total agent execution time in milliseconds.

        Falls back to ``time.perf_counter()`` if the agent hasn't finished
        yet (e.g., when reading timing after an exception).
        """
        if self._agent_start == 0.0:
            return 0
        end = self._agent_end if self._agent_end else time.perf_counter()
        return int((end - self._agent_start) * 1000)

    @property
    def llm_call_count(self) -> int:
        """Number of LLM calls made during this agent run."""
        return len(self._llm_starts)

    @property
    def llm_total_ms(self) -> int:
        """Total LLM execution time in milliseconds."""
        if not self._llm_starts:
            return 0
        starts = self._llm_starts
        ends = self._llm_ends[: len(starts)]
        # Pad ends list if some LLM calls haven't finished
        now = time.perf_counter()
        while len(ends) < len(starts):
            ends.append(now)
        total = sum(
            int((e - s) * 1000) for s, e in zip(starts, ends)
        )
        return total

    @property
    def tool_calls(self) -> list[dict[str, Any]]:
        """List of completed tool calls with name and duration_ms.

        Returns a copy so callers cannot mutate internal state."""
        return list(self._tool_results)

    @property
    def tool_call_count(self) -> int:
        """Number of completed tool calls during this agent run."""
        return len(self._tool_results)
