"""
Seed multiple editorial blog posts directly into the database.
Run: python scripts/seed-editorial-posts.py

This seeds 3 professional posts about AI Agents in production:
1. How to Apply AI Agents to Real Production Projects
2. Production Patterns for Multi-Agent Systems
3. Building Reliable AI Agent Pipelines
"""

import sys
import os
import uuid
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "AI_LAB_DATABASE_URL",
    "postgresql+psycopg://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal",
)

POSTS = [
    {
        "title": "How to Apply AI Agents to Real Production Projects",
        "slug": "apply-ai-agents-real-production-projects",
        "excerpt": "A practical guide to moving AI agents from proof-of-concept to production — covering architecture decisions, observability, error handling, and the human-in-the-loop patterns that actually work.",
        "tags": ["AI Agents", "Production", "Engineering"],
        "author_name": "AI Lab",
        "reading_time": 14,
        "content_markdown": """## Introduction

AI agents have moved from research papers into the mainstream. Every engineering team I talk to is building something with agents — whether it is a coding assistant, a customer support bot, or an internal workflow automation. But there is a gap between a working prototype and a system you can trust in production.

This guide shares the patterns and practices that separate toy demos from production-grade agent systems. These are lessons from building agentic systems that handle real user traffic, real data, and real consequences when something goes wrong.

## Start with the Boundary, Not the Agent

The most common mistake teams make is reaching for an agent framework before defining the system boundary. Before you write a single tool definition, answer these questions:

**What is the agent allowed to do?** Define the scope explicitly. An agent that can read any database table is very different from one that can only query a curated read-model.

**What is the agent NOT allowed to do?** This is more important. Destructive operations, billing actions, and user data exports should be gated behind human approval.

**What happens when the agent is uncertain?** A production agent must know when to ask for help rather than guess.

Define these boundaries in code, not in documentation. Use a typed permission system:

```typescript
interface AgentPermissions {
  canRead: string[];       // resource patterns
  canWrite: string[];      // resource patterns
  requiresApproval: string[]; // actions needing human
  maxTokens: number;
  allowedModels: string[];
}
```

Every tool invocation checks against this permission object. If a tool is not listed, the agent cannot call it.

## Choose the Right Agent Topology

Not every problem needs a multi-agent system. In fact, most problems do not. Here is a decision framework:

| Complexity | Topology | Example |
|---|---|---|
| Single-step, deterministic | Direct function call | Formatting, validation |
| Multi-step, linear | Single agent with tools | Data extraction pipeline |
| Multi-step, branching | Supervisor + workers | Document processing |
| Open-ended, creative | Multi-agent debate | Research synthesis |
| High-stakes | Human-in-the-loop | Code review, financial ops |

Start with the simplest topology that solves the problem. Add complexity only when you have evidence that the simpler approach fails.

## Observability Is Not Optional

Agents are non-deterministic by nature. You cannot debug them by reading logs alone. You need:

**Traces, not just logs.** Every agent invocation should produce a trace showing the exact sequence of tool calls, LLM responses, and intermediate reasoning. Tools like Langfuse, Helicone, or a custom OpenTelemetry exporter work well.

**Cost tracking per-invocation.** LLM calls are not free. Track token usage per user, per session, and per action type. Set budget limits and alert when a single invocation costs more than expected.

**A replay system.** When an agent produces a bad result, you need to replay the exact same inputs to debug. Store the full conversation context — messages, tool results, system prompts — in a replayable format.

```python
# Example: structured trace for every agent run
{
    "trace_id": "abc123",
    "session_id": "session_456",
    "user_id": "user_789",
    "steps": [
        {
            "step": 1,
            "type": "llm_call",
            "model": "gpt-4o",
            "input_tokens": 450,
            "output_tokens": 120,
            "duration_ms": 2300
        },
        {
            "step": 2,
            "type": "tool_call",
            "tool": "search_docs",
            "duration_ms": 800,
            "result_truncated": True
        }
    ],
    "total_cost": 0.008,
    "total_duration_ms": 8500,
    "final_status": "success"
}
```

## Error Handling: Plan for Failure

LLMs fail in ways traditional software does not. They hallucinate, misunderstand instructions, get stuck in loops, and exceed token limits. Your system must handle all of these gracefully.

**Retry with backoff.** LLM API calls fail for transient reasons. Implement exponential backoff with jitter. But also set a maximum retry count — if the API is returning garbage, retrying will not help.

**Timeout every agent run.** Agents can spin indefinitely. Set a hard timeout per invocation (e.g., 60 seconds). When the timeout fires, log the partial state and return a graceful error to the user.

**Detect loops.** Agents sometimes repeat the same tool call with the same result. Track the last N tool-result pairs and break the loop when you detect a cycle. Inform the user instead of burning tokens.

**Graceful degradation.** When an agent fails, fall back to a simpler deterministic path. For example, if the multi-step research agent fails, fall back to a single LLM call with a static knowledge base.

```typescript
async function runAgentWithFallback(input: string): Promise<Result> {
  try {
    return await runFullAgent(input);
  } catch (error) {
    console.warn("Full agent failed, falling back:", error);
    return await runSimpleLLM(input);
  }
}
```

## Human-in-the-Loop: Design the Handoff

Production agents need humans in the loop for high-stakes decisions. The handoff design determines whether your system feels helpful or frustrating.

**Async review queues.** For actions like publishing content or approving code changes, put the agent's proposal into a review queue. The human reviews it when convenient. The agent can work on other tasks in the meantime.

**Inline approval.** For faster workflows (e.g., confirming a parameter value before running a destructive operation), use inline approval. The agent pauses and asks a yes/no question with context.

**Escalation paths.** Define what happens when the human does not respond. Timeout, fail-safe (reject the action), and notify again after a configurable period.

## Testing Agent Systems

Testing agents requires a different approach from traditional software testing.

**Scenario-based testing.** Define realistic scenarios with expected outcomes. For example: "User asks to search documentation for 'deployment' and expects 3 relevant results with links."

**Adversarial testing.** Test edge cases that trigger bad behavior. Empty inputs, contradictory instructions, requests to bypass constraints. The agent should handle these gracefully.

**Regression test suite.** Record real agent runs that produced correct results and replay them after every prompt or tool change. This catches regressions before they reach users.

**Cost benchmarks.** Track cost per scenario. A prompt change that improves quality by 5% but triples cost is not always the right trade-off.

## Conclusion

Building AI agents for production is not about choosing the right framework or the newest model. It is about designing the right boundaries, building observability from day one, handling failures gracefully, and knowing when to involve humans.

Start simple. Add complexity when you have data that justifies it. Test everything. And always ask: what happens when this agent makes a mistake?
""",
    },
    {
        "title": "Production Patterns for Multi-Agent Systems",
        "slug": "production-patterns-multi-agent-systems",
        "excerpt": "Deep dive into architectural patterns for systems with multiple AI agents — supervisor hierarchies, debate protocols, routing strategies, and the coordination patterns that scale.",
        "tags": ["AI Agents", "Architecture", "Engineering"],
        "author_name": "AI Lab",
        "reading_time": 16,
        "content_markdown": """## Why Multi-Agent?

A single agent with tools can handle many tasks, but there is a ceiling. When your system needs to reason across multiple domains, maintain long-running state, or handle conflicting objectives, a single agent struggles. The agent's context window fills up, its reasoning degrades on complex chains, and one bad step poisons the rest of the run.

Multi-agent systems solve this by decomposing complexity. Each agent owns a narrow responsibility: one searches documentation, another writes code, a third reviews for security issues. The coordination between them becomes the hard part.

This guide covers the architectural patterns that make multi-agent systems work in production.

## Pattern 1: Supervisor Hierarchy

The most common and battle-tested pattern. A supervisor agent receives the user's request, decomposes it into sub-tasks, dispatches each to a specialist worker, and synthesises the results.

```
User Request
    |
Supervisor Agent
    |
    +-- Worker A (Research)
    +-- Worker B (Code generation)
    +-- Worker C (Review)
    |
    v
Synthesised Response
```

**When to use:** Clear decomposition boundaries. Each subtask has a well-defined input and output.

**Design considerations:**

- The supervisor's prompt is the most important prompt in the system. It must be explicit about delegation rules: when to spawn a worker, how to interpret results, and when to ask for clarification instead of guessing.
- Workers should be stateless. All context needed for the task should be passed in the invocation. This makes workers testable and replaceable.
- The supervisor should timeout if workers do not respond within a reasonable window. A stuck worker should not block the entire system.

```typescript
interface SupervisorConfig {
  maxWorkers: number;         // max parallel workers
  workerTimeoutMs: number;    // per-worker timeout
  retryFailedWorkers: boolean;
  synthesisStrategy: "sequential" | "parallel" | "debate";
}
```

## Pattern 2: Debate and Consensus

Two or more agents with potentially different perspectives debate a topic and converge on a consensus answer. This is useful for tasks where correctness is critical and different reasoning paths can uncover blind spots.

```
Question
    |
    +-- Agent A (optimistic)
    |
    +-- Agent B (skeptical)
    |
    +-- Agent C (fact-checker)
    |
    v
Consensus (agreement >= 2/3)
```

**When to use:** High-stakes decisions where a single wrong answer causes real harm. Code review, financial analysis, medical advice triage.

**Design considerations:**

- Each agent should have a different system prompt or perspective. If all agents share the same prompt and model, you are just paying more for the same answer.
- Define a clear stopping condition. When 2 out of 3 agents agree, you can stop. Requiring all 3 to agree may never terminate.
- The moderator (a lightweight agent or deterministic function) evaluates the debate and produces the final answer. It does not need to be a full LLM — a prompt template that asks "which argument is best supported by evidence?" works.

## Pattern 3: Routing Gateway

A lightweight router classifies incoming requests and dispatches to the appropriate agent or workflow. This is like a load balancer for agents.

```
Request
    |
Router (classifier)
    |
    +-- Agent for coding questions
    +-- Agent for documentation
    +-- Agent for configuration
    +-- Fallback: human handoff
```

**When to use:** Your system handles multiple distinct task types and each needs a different agent configuration.

**Design considerations:**

- The router should be fast and cheap. Use a small classification model (e.g., GPT-4o-mini) or even a keyword-based classifier for common paths.
- The router's confidence score determines the next step. High-confidence requests go directly to the specialist. Medium-confidence requests add a confirmation step. Low-confidence requests escalate to a human.
- Log routing decisions to measure the accuracy of your classifier over time.

## Pattern 4: Tool Composition

Instead of routing between agents, agents share a common tool ecosystem. Each agent can call any tool, but the tool itself is an agent that does one thing well.

```
Agent A ---> Tool X (specialist agent)
Agent B ---> Tool X (same specialist)
Agent C ---> Tool Y (different specialist)
```

**When to use:** You have reusable specialist capabilities that multiple agents need. For example, a "search codebase" tool that works regardless of which agent calls it.

**Design considerations:**

- Tool agents must be idempotent. Calling the same tool with the same inputs must produce the same result.
- Tool agents should have guardrails. A search tool agent should refuse to delete data, even if the calling agent asks nicely.
- Cache tool results aggressively. If Agent A and Agent B both call the search tool with the same query, the second call should return cached results.

## Observability in Multi-Agent Systems

Each pattern introduces new failure modes. Supervisor hierarchies can deadlock. Debate systems can loop indefinitely. Routing gateways can misclassify.

**Trace every message.** Every message between agents should be recorded with timing, token count, and routing metadata. Use OpenTelemetry spans with parent-child relationships to reconstruct the full interaction graph.

**Visualise the graph.** A text log is not enough. Use a trace viewer that shows the agent call graph — which agent called which, when, and how long each step took.

**Alert on anomalies.** Too many routing hops, unusually long debate cycles, or high token usage per request are signs that something is wrong.

```python
# Alert thresholds for multi-agent systems
ALERTS = {
    "max_agents_per_request": 10,      # more than this is likely a loop
    "max_tokens_per_request": 50000,  # cost guardrail
    "max_duration_seconds": 120,      # user-facing timeout
    "router_confidence_below": 0.4,   # likely misclassification
}
```

## Conclusion

Multi-agent systems are powerful but introduce coordination complexity. Start with a simple supervisor hierarchy before adding debate or routing patterns. Invest in observability from day one — you will need it when agents interact in unexpected ways.

The right pattern depends on your failure tolerance. If mistakes are expensive, use debate and consensus. If speed matters, use a routing gateway. If you need reusable specialists, use tool composition.

And always remember: a well-designed single agent beats a poorly designed multi-agent system every time.
""",
    },
    {
        "title": "Building Reliable AI Agent Pipelines",
        "slug": "building-reliable-ai-agent-pipelines",
        "excerpt": "How to build agent pipelines that handle failures gracefully, maintain state across steps, and produce consistent results — using patterns from production data engineering.",
        "tags": ["AI Agents", "MCP", "Production"],
        "author_name": "AI Lab",
        "reading_time": 12,
        "content_markdown": """## The Pipeline Mindset

Most agent systems are built as interactive chatbots: user sends a message, agent responds, conversation continues. This works for chat, but many production use cases need batch processing — processing thousands of documents, analysing codebases, or generating reports overnight.

For these workloads, you need a pipeline. A pipeline breaks the work into discrete stages, processes items in parallel, handles failures per-item rather than per-batch, and provides visibility into every step.

This guide adapts proven data engineering patterns to agentic workloads.

## Stage 1: Ingestion and Validation

Every pipeline starts with input. Raw inputs are unreliable — they come in different formats, with missing fields, unexpected encoding, or malicious content.

**Define a strict input schema.** Use Zod, Pydantic, or TypeScript interfaces to define exactly what your pipeline accepts. Reject inputs that do not match the schema before they reach any agent.

```typescript
import { z } from "zod";

const PipelineInputSchema = z.object({
  documentId: z.string().uuid(),
  content: z.string().min(1).max(100_000),
  sourceType: z.enum(["markdown", "html", "plaintext"]),
  metadata: z.record(z.string()).optional(),
});
```

**Validate at the boundary.** Run validation as the very first step, before any LLM call. A validation failure should produce a clear error message and not consume any tokens.

**Normalise inputs.** Convert all inputs to a canonical format before processing. This simplifies downstream agents — they only need to handle one format.

## Stage 2: Parallel Processing with Workers

Once inputs are validated, dispatch them to worker agents. Workers are ephemeral — they process one item and terminate. This makes the system resilient: a failing worker does not affect other items.

```typescript
interface WorkerPool {
  maxConcurrency: number;
  queue: string[];
  active: Map<string, Worker>;
  results: Map<string, WorkerResult>;
}
```

**Design workers as pure functions.** A worker agent receives input context and returns output. It should not have side effects. This makes workers testable and allows retries without side-effect duplication.

**Set per-worker resource limits.** Token budgets, time limits, and retry counts should be configured per worker type. A research worker needs different limits than a formatting worker.

**Isolate worker state.** Each worker runs in its own context. No shared memory, no global state. Communication happens through the pipeline's result store, not through agent-to-agent messages.

## Stage 3: Checkpointing and Recovery

Pipelines fail. The database goes down, the LLM API returns errors, a worker crashes mid-processing. Your pipeline must recover without reprocessing all items.

**Checkpoint after each stage.** Store the results of each pipeline stage in a durable store (PostgreSQL, S3, or Redis). On restart, query which items have completed which stages and resume from the last checkpoint.

```python
# Checkpoint schema
checkpoint = {
    "pipeline_id": "pipe_abc",
    "item_id": "doc_123",
    "stage": "extraction",
    "status": "completed",  # or "failed", "in_progress"
    "output": { ... },
    "tokens_used": 4500,
    "started_at": "2026-06-01T10:00:00Z",
    "completed_at": "2026-06-01T10:00:12Z",
}
```

**Idempotent stages.** Each stage must be safe to run multiple times. If you checkpoint after stage A and the pipeline crashes during stage B, rerunning stage A should produce the same result or be a no-op.

**Handle partial failures gracefully.** If item 5 out of 1000 fails, do not discard the entire batch. Mark item 5 as failed, log the error, and continue processing the remaining items. A report at the end shows: 995 succeeded, 4 failed, 1 skipped.

## Stage 4: Quality Gates

Not every agent output is good enough for production. Insert quality gates between pipeline stages to catch bad outputs early.

**Automated quality checks:**
- Length validation: is the output the expected minimum length?
- Format validation: does the output match the expected schema?
- Keyword presence: does the output contain expected sections?
- Toxicity check: does the output contain inappropriate content?

**Sampling-based human review.** For high-volume pipelines, automate the quality gates but sample a percentage for human review. Log the human verdict to improve the quality gates over time.

```typescript
interface QualityGate {
  name: string;
  check: (output: unknown) => boolean | Promise<boolean>;
  severity: "warn" | "block";
  onFailure: "retry" | "skip" | "flag_for_review";
}
```

## Stage 5: Output Assembly

The final stage assembles processed items into the output format your consumers expect. This is the simplest stage and should be deterministic.

- Combine results into a batch output file
- Write results to a database
- Trigger downstream workflows via webhook
- Generate a summary report with per-item status

The output stage should also produce a pipeline manifest: a JSON document that lists every input item, its processing status, token usage, timing, and any errors. This manifest is your audit trail.

## Operational Patterns

**Dead letter queue.** Items that fail after maximum retries go to a dead letter queue. A human reviews the queue periodically and decides whether to fix the input and retry or discard the item.

**Gradual rollout.** When you change a prompt or model, do not process all items with the new configuration. Process a small sample first, verify quality, then ramp up.

**Cost budgeting.** Set a maximum cost per pipeline run. If the budget is exceeded, pause the pipeline and alert. This prevents runaway spending on a misconfigured pipeline.

**Pipeline telemetry.** Export metrics for throughput, error rate, latency per stage, and token usage. Set up dashboards and alerts. A pipeline with no monitoring is a pipeline waiting to fail.

```yaml
# Prometheus-style metrics
agent_pipeline_items_total{pipeline="doc_processor", status="success"} 995
agent_pipeline_items_total{pipeline="doc_processor", status="failure"} 4
agent_pipeline_duration_seconds{pipeline="doc_processor", stage="extraction"} 12.5
agent_pipeline_tokens_total{pipeline="doc_processor"} 450000
```

## Conclusion

Building reliable agent pipelines requires shifting from a chat mindset to a data engineering mindset. Define strict schemas, checkpoint after every stage, design idempotent workers, and insert quality gates.

The pipeline that processes 10,000 items without human intervention is worth more than a dozen impressive chatbot demos. Reliability is the feature that separates production systems from experiments.

Start with a simple linear pipeline. Add parallelism when throughput demands it. Add quality gates when you catch your first bad output. And always, always checkpoint.
""",
    },
]


def seed_posts():
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        for i, post in enumerate(POSTS):
            # Check for existing post
            existing = conn.execute(
                text("SELECT id FROM blog_posts WHERE slug = :slug"),
                {"slug": post["slug"]},
            ).fetchone()
            if existing:
                print(f"  Skipping '{post['slug']}' -- already exists (id={existing[0]})")
                continue

            now = datetime.now(timezone.utc)
            # Stagger publish dates so they appear in a nice order
            published_at = now - timedelta(hours=i * 24 + 1)
            post_id = str(uuid.uuid4())

            conn.execute(
                text("""
                    INSERT INTO blog_posts (id, title, slug, excerpt, content_markdown,
                        author_name, status, published_at)
                    VALUES (:id, :title, :slug, :excerpt, :content_markdown,
                        :author_name, :status, :published_at)
                """),
                {
                    "id": post_id,
                    "title": post["title"],
                    "slug": post["slug"],
                    "excerpt": post["excerpt"],
                    "content_markdown": post["content_markdown"],
                    "author_name": post["author_name"],
                    "status": "published",
                    "published_at": published_at,
                },
            )
            print(f"  [OK] Created: {post['title']} (id={post_id})")

            # Tags
            for tag_name in post["tags"]:
                tag_id = str(uuid.uuid4())
                tag_slug = tag_name.lower().replace(" ", "-")
                result = conn.execute(
                    text("""
                        INSERT INTO blog_tags (id, slug, name, created_at)
                        VALUES (:id, :slug, :name, :now)
                        ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name
                        RETURNING id
                    """),
                    {"id": tag_id, "slug": tag_slug, "name": tag_name, "now": now},
                ).fetchone()
                resolved_tag_id = result[0]

                conn.execute(
                    text("""
                        INSERT INTO blog_post_tags (post_id, tag_id)
                        VALUES (:post_id, :tag_id)
                        ON CONFLICT DO NOTHING
                    """),
                    {"post_id": post_id, "tag_id": resolved_tag_id},
                )
                print(f"    Tag: {tag_name}")

    print("\nDone! New posts live at:")
    for post in POSTS:
        print(f"  /blog/{post['slug']}")


if __name__ == "__main__":
    seed_posts()
