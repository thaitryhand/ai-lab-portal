"""
Seed 3 more editorial blog posts about AI engineering.
Run: python scripts/seed-editorial-posts-2.py
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
        "title": "MCP in Production: Scaling Model Context Protocol Across Your Team",
        "slug": "mcp-in-production-scaling-across-team",
        "excerpt": "How to design, deploy, and maintain MCP servers at team scale — covering server discovery, authentication, rate limiting, monitoring, and the organizational patterns that make MCP adoption stick.",
        "tags": ["MCP", "Production", "Engineering"],
        "author_name": "AI Lab",
        "reading_time": 14,
        "content_markdown": """## Beyond the First MCP Server

Building your first MCP server is straightforward. Scaling MCP across a team of ten engineers with dozens of servers is a different challenge entirely. This guide covers what happens after the prototype works and you need to make MCP a reliable part of your development infrastructure.

## Server Discovery and Registry

When every team runs their own MCP servers, the first problem is discovery. How does an engineer know what servers are available and what tools each exposes?

**A central registry.** Maintain a JSON manifest in a shared repository (or a database) that lists every MCP server, its purpose, maintainer, and health status. Codex CLI and other MCP hosts can query this registry to discover available tools.

```json
{
  "servers": [
    {
      "name": "docs-search",
      "description": "Search internal documentation",
      "maintainer": "team-platform",
      "command": "node",
      "args": ["servers/docs-search/dist/index.js"],
      "status": "stable",
      "tools": ["search_docs", "get_doc", "list_topics"]
    }
  ]
}
```

**Health checks for every server.** Each MCP server should expose a health endpoint (either via HTTP or a dedicated `health` tool). The registry periodically pings every server and marks unhealthy ones. Engineers see live status before choosing a server.

**Versioning.** MCP servers evolve. Use semantic versioning for server releases. The registry tracks which version is deployed and what changes each version introduces. Engineers configure their MCP host to pin to a specific version or follow the latest.

## Authentication and Authorization

Not every tool should be available to every engineer. Financial operations, production deployments, and customer data queries need access control.

**Per-tool permissions.** Define access levels per tool within each MCP server:

```typescript
interface ToolAccess {
  name: string;
  minRole: "reader" | "contributor" | "admin";
  auditLevel: "none" | "log" | "require_approval";
}
```

**User identity propagation.** When Codex CLI calls an MCP tool, it should pass the user's identity via an environment variable or a dedicated `x-mcp-user-identity` header. The MCP server checks permissions before executing.

**Audit logging.** Every tool invocation that touches production data or performs mutations should be logged with user identity, timestamp, tool name, and parameters. This audit trail is essential for compliance and debugging.

## Rate Limiting and Cost Control

LLM-powered MCP tools are expensive. A single misconfigured agent calling `search_docs` in a loop can burn through your API budget in minutes.

**Per-user rate limits.** Track token usage per user per hour. When a user exceeds their limit, the MCP server returns a rate-limit error instead of consuming more tokens.

```python
RATE_LIMITS = {
    "default": {
        "requests_per_minute": 30,
        "tokens_per_hour": 100_000,
    },
    "admin": {
        "requests_per_minute": 100,
        "tokens_per_hour": 500_000,
    },
}
```

**Cost attribution.** Tag every tool invocation with the user's team and project. At the end of the month, you can see which teams are spending the most on AI tooling and whether the investment is paying off.

**Caching.** Many tool invocations return the same result. Cache aggressively. A search tool that returns documentation should cache results for at least five minutes. A code-analysis tool should cache results per commit hash.

## Monitoring and Alerting

MCP servers fail silently. Unlike a web API where a 500 error is obvious, an MCP server that returns garbage results or times out can go unnoticed for hours.

**Key metrics to track:**

- Invocation count per tool per hour
- Median and p99 latency per tool
- Error rate per tool
- Token consumption per user and per tool
- Cache hit rate

**Set up alerts:**

- Latency p99 above 10 seconds for any tool
- Error rate above 5% in any five-minute window
- Any tool returning empty results repeatedly
- Token consumption spike (2x normal in an hour)

**Dashboard.** Build a simple dashboard showing MCP health across all servers. A red/green status for each server, with drill-down to per-tool metrics.

```yaml
# Prometheus-style metrics
mcp_tool_invocations_total{server="docs-search", tool="search_docs"} 1423
mcp_tool_latency_seconds{server="docs-search", tool="search_docs", quantile="0.99"} 4.2
mcp_tool_errors_total{server="docs-search", tool="search_docs"} 3
mcp_tool_tokens_total{server="docs-search", tool="search_docs"} 450000
```

## Organizational Patterns

MCP adoption succeeds or fails based on organizational practices, not technology.

**Champion model.** Designate one engineer per team as the MCP champion. They own their team's servers, review pull requests to the registry, and advocate for MCP within their team.

**Server ownership.** Every MCP server must have a named maintainer and at least one backup. When the maintainer is on vacation, the backup handles issues.

**RFC process for new servers.** Before adding a server to the registry, require a lightweight RFC covering: the problem it solves, the tools it exposes, the expected token cost per invocation, and a security review.

**Regular deprecation.** MCP servers that go unused for 90 days are deprecated. Their maintainers are notified, and after 30 more days, the server is removed from the registry. This prevents registry bloat.

## Conclusion

Scaling MCP across a team requires more infrastructure than running a single server, but the investment pays off. A well-maintained MCP ecosystem gives every engineer access to powerful AI-assisted tools without the maintenance burden of running everything themselves.

The key patterns are: central discovery via a registry, authentication per tool, rate limiting for cost control, comprehensive monitoring, and clear organizational ownership.

Start with these patterns early. Retrofitting access control and monitoring after adoption takes hold is much harder than building them in from the beginning.
""",
    },
    {
        "title": "Agent Observability: Tracing, Monitoring, and Debugging AI Systems",
        "slug": "agent-observability-tracing-monitoring-debugging",
        "excerpt": "A practical guide to building observability into AI agent systems — from structured tracing and cost tracking to automated alerting and replay debugging for non-deterministic LLM workflows.",
        "tags": ["AI Agents", "Engineering", "Production"],
        "author_name": "AI Lab",
        "reading_time": 13,
        "content_markdown": """## Why Agent Observability Is Different

Traditional software observability assumes determinism: the same input produces the same output every time, so you can reason about failures by replaying requests. AI agents break this assumption. An agent might succeed nine times out of ten and fail on the tenth for reasons that are invisible in logs alone.

This guide covers the observability patterns that work for non-deterministic, LLM-driven systems.

## Structured Tracing: The Foundation

Every agent invocation must produce a structured trace. Not a log line, not a debug print statement, but a JSON-serialisable trace that captures the full execution graph.

**What a trace needs:**

- A unique trace ID and session ID
- Every LLM call with model, input/output tokens, temperature, and duration
- Every tool call with parameters, result (or error), and duration
- The agent's internal reasoning at each step
- The final response and any error messages
- Total cost and duration

```python
# Example trace schema
trace = {
    "trace_id": "trc_9k3m2n1p",
    "session_id": "sess_abc456",
    "user_id": "user_789",
    "started_at": "2026-06-01T10:00:00Z",
    "steps": [
        {
            "step": 1,
            "type": "llm_call",
            "model": "gpt-4o",
            "system_prompt_hash": "sha256:abc...",
            "input_tokens": 450,
            "output_tokens": 120,
            "duration_ms": 2300,
            "temperature": 0.7,
        },
        {
            "step": 2,
            "type": "tool_call",
            "tool": "search_docs",
            "query": "deployment configuration",
            "result_preview": "3 results found...",
            "duration_ms": 800,
        },
        {
            "step": 3,
            "type": "reasoning",
            "content": "Based on the docs, I should recommend...",
        },
    ],
    "final_status": "success",
    "total_cost_usd": 0.008,
    "total_duration_ms": 8500,
}
```

## Storing and Querying Traces

Logging traces to stdout is not enough. You need a trace store that supports querying, filtering, and aggregation.

**Choose a store.** OpenSearch, ClickHouse, or even PostgreSQL with JSONB columns work well. The key requirements are: fast writes (you will write a lot), JSON querying, and time-range filtering.

**Index the important fields.** At minimum, index: trace_id, session_id, user_id, model, final_status, and started_at. If your trace volume is high, partition by date.

**Sampling strategy.** In high-volume systems, storing every trace is expensive. Use head-based sampling: store 100% of traces with errors or high latency, and 1-10% of successful traces. This gives you full coverage of failures while controlling costs.

## Cost Tracking Per Invocation

AI agents make observability more urgent because they cost real money to run. You need per-invocation cost tracking from day one.

**Token counting.** Count input and output tokens for every LLM call. Multiply by the model's per-token pricing to get the monetary cost.

**Attribution.** Tag every trace with user_id, team, project, and feature. This lets you answer: "How much did the AI search feature cost our platform team this month?"

**Budget alerts.** Set a daily budget per team per feature. When spend exceeds 80% of the budget, send a warning. When it exceeds 100%, throttle or pause the feature.

```python
budget_alerts = {
    "platform.search": {
        "daily_budget": 50.00,  # USD
        "warn_at": 0.8,
        "stop_at": 1.0,
    }
}
```

## Debugging Non-Deterministic Failures

The hardest bugs in agent systems are the ones that only happen sometimes. You need tools specifically designed for non-deterministic debugging.

**Replay with the same seed.** Many LLM providers support a `seed` parameter that makes outputs more deterministic. When you identify a problematic trace, replay it with the same seed, same messages, and same system prompt to reproduce the issue.

**Diff traces.** Compare a failing trace against a successful trace for the same user request. The diff should highlight where the agents diverged: a different tool was called, the LLM returned different reasoning, or a timeout caused a different code path.

**Failure clustering.** Group failures by error message, tool name, or user intent. If 50% of failures are caused by the search tool returning empty results, you know where to focus your debugging.

## Automated Alerting

Don't wait for users to report problems. Set up automated alerts that fire when your agent system behaves abnormally.

**Alert on metrics:**

- Error rate > 5% in any 5-minute window
- p99 latency > 30 seconds
- Cost per invocation > 2x the weekly average
- Any tool returning errors for 3 consecutive calls
- Agent loop detection: more than 20 steps for a single invocation

**Alert on business outcomes:**

- User satisfaction rating drops below 4/5
- Task completion rate drops below 80%
- Number of escalation-to-human increases by 50%

## Building an Observability Culture

Tools are not enough. You need a culture that treats observability as a first-class requirement.

**Trace reviews.** Include trace inspection in code reviews for agent prompt changes. A reviewer should be able to see: "Does this prompt change produce better traces? Does it add useful reasoning steps?"

**Runbooks.** Document what to do when each alert fires. A runbook for "high error rate on search tool" might say: check the vector database status, verify the embedding model is responding, look for recent deployment changes.

**Post-mortems.** When an agent produces a harmful result, write a post-mortem that includes the full trace, the root cause, and what observability gap allowed it to reach production.

## Conclusion

Agent observability is not optional. The non-deterministic nature of LLMs makes traditional debugging approaches insufficient. Build structured tracing from day one, track costs per invocation, set up automated alerting, and invest in the tooling and culture needed to debug non-deterministic failures.

The teams that invest in observability early are the ones that can ship agent features confidently. Everyone else is debugging in the dark.
""",
    },
    {
        "title": "From Notebook to Production: A Framework for Shipping AI Features",
        "slug": "from-notebook-to-production-ai-framework",
        "excerpt": "A repeatable framework for taking AI features from Jupyter notebook experimentation to production deployment — covering evaluation gates, prompt management, A/B testing, and gradual rollout strategies.",
        "tags": ["AI Agents", "Production", "Engineering"],
        "author_name": "AI Lab",
        "reading_time": 15,
        "content_markdown": """## The Notebook Trap

Every AI project starts the same way: a Jupyter notebook, an API key, and a feeling of magic when the model returns exactly what you wanted. The notebook works. You demo it to your team. Everyone is excited. Then comes the hard part: shipping it to production.

The gap between a notebook demo and a production AI feature is wider than most teams expect. The model that performed beautifully on three hand-picked examples fails on real-world data. The prompt that seemed perfect breaks when users ask unexpected questions. The latency that was imperceptible in a notebook becomes a problem at scale.

This framework bridges that gap. It is a repeatable process for taking AI features from experimentation to production deployment.

## Stage 1: Define the Success Criteria

Before you write a single line of prompt, define what success looks like. This is the most skipped step and the most important one.

**Quantitative criteria:**
- Accuracy: what percentage of outputs must be correct?
- Hallucination rate: what percentage of outputs can contain made-up information?
- Latency: what is the maximum acceptable response time?
- Cost: what is the maximum acceptable cost per invocation?

**Qualitative criteria:**
- Tone: should the output be formal, conversational, or technical?
- Structure: should the output follow a specific template?
- Safety: what topics should the AI refuse to discuss?

```python
evaluation_criteria = {
    "accuracy": {"min": 0.95, "metric": "exact_match"},
    "hallucination_rate": {"max": 0.01},
    "latency_p99_ms": {"max": 5000},
    "cost_per_invocation_usd": {"max": 0.05},
    "tone": "technical_but_accessible",
}
```

**Define the evaluation dataset.** Collect 50-200 real-world examples that represent the full range of inputs your system will see. Include edge cases: empty inputs, very long inputs, inputs with special characters, inputs in different languages.

## Stage 2: Prompt Development and Versioning

Prompts are code. Treat them with the same rigor.

**Version control for prompts.** Store prompts in a dedicated directory alongside your code. Each prompt gets a file, a version number, and a changelog. Never hardcode prompts in source files.

```
prompts/
  search_agent/
    v1_system.md
    v2_system.md
    v1_user_template.md
  summarizer/
    v1_system.md
```

**Prompt testing.** Write unit tests for your prompts. Test edge cases: very short inputs, very long inputs, inputs with PII, inputs with ambiguous instructions. A prompt test checks that the output contains required sections and does not contain prohibited content.

**Prompt vs code coupling.** The prompt and the code that calls the LLM should be loosely coupled. The code handles input preparation, output parsing, error handling, and fallbacks. The prompt handles the model's behavior. This separation lets you iterate on prompts without touching code.

## Stage 3: Evaluation Gates

Every change to your AI feature — whether a prompt tweak, a model upgrade, or a new tool — must pass evaluation gates before reaching production.

**Gate 1: Offline evaluation.** Run your evaluation dataset against the new version. Compare results against the previous version. If accuracy drops or hallucination rate increases, the change is rejected.

```python
def evaluate(prompt_version: str) -> EvaluationResult:
    results = []
    for example in evaluation_dataset:
        output = run_agent(example.input, prompt_version)
        results.append(compare(output, example.expected))
    return aggregate(results)
```

**Gate 2: Shadow mode.** Deploy the new version alongside the current production version. The new version processes real requests but its output is not shown to users. Compare the outputs. If the new version produces worse results, it is rejected.

**Gate 3: Canary deployment.** Deploy the new version to 1% of users. Monitor metrics for 24 hours. If all metrics are healthy, ramp to 5%, then 25%, then 100%. Roll back immediately if any metric degrades.

```yaml
# Canary deployment config
canary:
  stages:
    - percentage: 1
      duration_hours: 24
      evaluation: monitor_all_metrics
    - percentage: 5
      duration_hours: 12
      evaluation: monitor_error_rate_and_latency
    - percentage: 25
      duration_hours: 12
      evaluation: monitor_all_metrics
    - percentage: 100
      duration_hours: 0
      evaluation: none
  rollback_triggers:
    - error_rate > 5%
    - latency_p99 > 10s
    - cost_per_invocation > 2x baseline
```

## Stage 4: Production Infrastructure

An AI feature needs different infrastructure than a traditional API endpoint.

**Fallback chain.** Always have a fallback. If the LLM API returns an error, use a simpler model. If the simpler model also fails, return a cached result or a graceful error message. Never show a raw error to the user.

```typescript
async function getAIResponse(input: string): Promise<Response> {
  try {
    return await callGPT4(input);
  } catch {
    console.warn("GPT-4 failed, falling back to GPT-4o-mini");
  }
  try {
    return await callGPT4Mini(input);
  } catch {
    console.warn("All LLMs failed, returning cached result");
    return getCachedResponse(input) ?? {
      status: "degraded",
      message: "AI service temporarily unavailable",
    };
  }
}
```

**Caching.** Cache results aggressively. Many AI requests are duplicates or near-duplicates. A cache hit saves cost and improves latency.

**Rate limiting.** Protect your AI budget from runaway usage. Set per-user, per-feature, and global rate limits.

**Timeout handling.** LLM APIs can hang. Set an aggressive timeout (10-30 seconds depending on the use case). When the timeout fires, log the partial result and return a graceful degradation.

## Stage 5: Monitoring and Iteration

Shipping the first version is not the end. Plan for continuous improvement.

**Feedback loop.** Collect user feedback on every AI response. A simple thumbs-up/thumbs-down lets you identify which responses are good and which are not. Investigate the negative feedback in bulk to find patterns.

**Drift detection.** Monitor your evaluation metrics over time. If accuracy drifts downward or hallucination rate drifts upward, you need to update your prompts or retrain your model.

**Regular re-evaluation.** Re-run your evaluation dataset monthly. A prompt that worked perfectly six months ago may degrade as the underlying model changes.

## Conclusion

Shipping AI features to production requires a systematic approach. Define success criteria before writing prompts. Version your prompts like code. Use evaluation gates to catch regressions. Build fallback chains for reliability. And monitor continuously to catch drift.

The notebook demo is where the journey starts, not where it ends. A repeatable framework turns AI experiments into reliable production features that teams can depend on.
""",
    },
]


def seed_posts():
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        for i, post in enumerate(POSTS):
            existing = conn.execute(
                text("SELECT id FROM blog_posts WHERE slug = :slug"),
                {"slug": post["slug"]},
            ).fetchone()
            if existing:
                print(f"  Skipping '{post['slug']}' -- already exists (id={existing[0]})")
                continue

            now = datetime.now(timezone.utc)
            published_at = now - timedelta(hours=i * 36 + 1)
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
                conn.execute(
                    text("""
                        INSERT INTO blog_post_tags (post_id, tag_id)
                        VALUES (:post_id, :tag_id)
                        ON CONFLICT DO NOTHING
                    """),
                    {"post_id": post_id, "tag_id": result[0]},
                )
                print(f"    Tag: {tag_name}")

    print("\nDone! New posts live at:")
    for post in POSTS:
        print(f"  /blog/{post['slug']}")


if __name__ == "__main__":
    seed_posts()
