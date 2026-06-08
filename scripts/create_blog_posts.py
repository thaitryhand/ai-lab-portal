"""Create 4 new blog posts for the AI Lab Portal."""

import uuid
from datetime import datetime, timezone
import sqlalchemy as sa

from backend.app.database import create_database_engine
from backend.app.settings import Settings

s = Settings(
    database_url="postgresql+psycopg://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal"
)
engine = create_database_engine(s)


def make_id():
    return "post_" + uuid.uuid4().hex[:30]


BLOG_POSTS = [
    {
        "id": make_id(),
        "slug": "pi-ecosystem-extending-agent-workflows",
        "title": "The Pi Ecosystem: Extending Agent Workflows with Community Packages",
        "author_name": "AI Lab Engineering",
        "status": "published",
        "published_at": datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc),
        "image_url": "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&q=80",
        "excerpt": "Explore the growing ecosystem of Pi coding agent extensions -- from subagents and task management to MCP integration, guardrails, and tool display enhancements that supercharge your agent workflow.",
        "content_markdown": (
            "## Beyond the Default Agent\n\n"
            "Pi coding agent ships with a powerful default workflow, but its true strength lies in the "
            "**extension ecosystem** that has grown around it. Community-built packages add everything from "
            "subagent orchestration to memory persistence, turning a capable agent into a customizable platform.\n\n"
            "This guide walks through the most impactful extensions and how they compose into production-grade workflows.\n\n"
            "---\n\n"
            "## 1. Subagents -- Divide and Conquer\n\n"
            "[**`pi-subagents`**](https://www.npmjs.com/package/@tintinweb/pi-subagents) "
            "lets you spawn and coordinate sub-agents that handle isolated subtasks. "
            "Instead of cramming everything into one context window, you delegate:\n\n"
            "- **Research tasks** -- spawn a subagent to explore a codebase while the main agent continues planning\n"
            "- **Parallel reviews** -- multiple subagents review different files simultaneously\n"
            "- **Specialized skills** -- each subagent loads only the tools it needs\n\n"
            "```bash\nnpm install @tintinweb/pi-subagents\n```\n\n"
            "## 2. Task Management -- Track Progress Systematically\n\n"
            "[**`pi-tasks`**](https://www.npmjs.com/package/@tintinweb/pi-tasks) "
            "adds a structured task/todo system to Pi. The agent creates, updates, and checks off tasks "
            "as it works -- giving you visibility into what has been done and what remains.\n\n"
            "```bash\nnpm install @tintinweb/pi-tasks\n```\n\n"
            "## 3. Persistent Memory -- Context That Survives Restarts\n\n"
            "[**`pi-memory-md`**](https://www.npmjs.com/package/pi-memory-md) "
            "stores agent memories as Markdown files. Unlike ephemeral in-context memory, "
            "this persists across sessions:\n\n"
            "- **Project conventions** -- remember naming patterns and architectural decisions\n"
            "- **User preferences** -- recall how you like tests structured\n"
            "- **Lessons learned** -- anti-patterns discovered during development\n\n"
            "```bash\nnpm install pi-memory-md\n```\n\n"
            "## 4. MCP Integration -- Connect Anything\n\n"
            "[**`pi-mcp-adapter`**](https://www.npmjs.com/package/pi-mcp-adapter) "
            "bridges Pi with the Model Context Protocol ecosystem. "
            "This opens up thousands of MCP servers for databases, APIs, browsers, and more.\n\n"
            "```bash\nnpm install pi-mcp-adapter\n```\n\n"
            "## 5. Guardrails -- Safety First\n\n"
            "[**`pi-guardrails`**](https://www.npmjs.com/package/@aliou/pi-guardrails) "
            "adds behavior constraints so your agent operates within defined boundaries.\n\n"
            "```bash\nnpm install @aliou/pi-guardrails\n```\n\n"
            "## 6. Better Tool Display -- See What the Agent Sees\n\n"
            "[**`pi-tool-display`**](https://www.npmjs.com/package/pi-tool-display) "
            "improves how tool calls and outputs are rendered in the terminal.\n\n"
            "## 7. More Extensions\n\n"
            "| Package | Purpose |\n"
            "|---------|---------|\n"
            "| [pi-augment](https://www.npmjs.com/package/pi-augment) | Hooks and augmentations for workflow customization |\n"
            "| [pi-multi-pass](https://github.com/hjanuschka/pi-multi-pass) | Multi-pass processing for improved output quality |\n"
            "| [pi-btw](https://github.com/dbachelder/pi-btw) | Utility extensions for context injection |\n"
            "| [pi-askuserquestion](https://github.com/ghoseb/pi-askuserquestion) | Let the agent ask for clarification |\n"
            "| [pi-agent-modes](https://www.npmjs.com/package/@danchamorro/pi-agent-modes) | Multiple operating modes |\n"
            "| [pi-vcc](https://www.npmjs.com/package/@sting8k/pi-vcc) | Workflow control and agent coordination |\n"
            "| [pi-amplike](https://www.npmjs.com/package/pi-amplike) | Amp-like workflow with permissions and handoff |\n\n"
            "## Getting Started Quickly\n\n"
            "If you are new to the Pi ecosystem, **[LazyPi](https://lazypi.org/)** bundles the most common "
            "extensions into a single setup.\n\n"
            "---\n\n"
            "## The Big Picture\n\n"
            "What makes this ecosystem powerful is **composability**:\n\n"
            "```\nPi Core\n-- pi-subagents    -- parallel task execution\n"
            "-- pi-tasks       -- progress tracking\n"
            "-- pi-memory-md   -- cross-session context\n"
            "-- pi-mcp-adapter -- database and API access\n"
            "-- pi-guardrails  -- safety boundaries\n"
            "-- pi-tool-display -- readable output\n```"
        ),
    },
    {
        "id": make_id(),
        "slug": "building-resilient-agent-workflows-pi-extensions",
        "title": "Building Resilient Agent Workflows: Tips from the Pi Community",
        "author_name": "AI Lab Engineering",
        "status": "published",
        "published_at": datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
        "image_url": "https://images.unsplash.com/photo-1518432031352-d6fc5c10da5a?w=1200&q=80",
        "excerpt": "Practical tips and battle-tested configurations for running Pi agents in production -- from context management and multi-agent setups to hooks, memories, and the hidden flags that make a difference.",
        "content_markdown": (
            "## Why Workflow Resilience Matters\n\n"
            "An agent that works perfectly for a 10-turn task can fall apart in a 200-turn session. "
            "Context degrades, tool calls go stale, and the agent drifts from its objective. "
            "The Pi community has developed patterns to address these challenges.\n\n"
            "---\n\n"
            "## 1. Context Management -- The #1 Challenge\n\n"
            "### Use `/compact` Strategically\n\n"
            "Don't wait until context is nearly full. **Compact after every milestone** -- "
            "when a feature is done, a test suite passes, or a review is complete.\n\n"
            "### Turn Off `/fast` for Complex Tasks\n\n"
            "Fast mode is excellent for quick iterations, but for tasks involving many tool calls "
            "or deep reasoning, disable it:\n\n```\n/fast off\n```\n\n"
            "The quality difference in long sessions is noticeable.\n\n"
            "### Leverage Memories for Long-Term Context\n\n"
            "```toml\n[features]\nmemories = true\n\n"
            "[memories]\ngenerate_memories = true\nuse_memories = true\n```\n\n"
            "Memories excel at storing project conventions, user preferences, and lessons learned.\n\n"
            "## 2. Multi-Agent Architecture\n\n"
            "Codex supports running multiple agents in parallel:\n\n"
            "```toml\n[agents]\nmax_depth = 1\nmax_threads = 12\n```\n\n"
            "| Scenario | Approach |\n|----------|----------|\n"
            "| Large refactor | Main agent plans, subagents execute per file |\n"
            "| Code review | Multiple agents review different modules |\n"
            "| Research + Implementation | One researches, another implements |\n\n"
            "## 3. Hooks -- Lifecycle Automation\n\n"
            "| Hook | Trigger | Use Case |\n"
            "|------|---------|----------|\n"
            "| `pre_tool` | Before a tool call | Validate inputs |\n"
            "| `post_tool` | After a tool call | Capture outputs |\n"
            "| `pre_llm` | Before LLM call | Inject context |\n"
            "| `post_llm` | After LLM call | Validate response |\n\n"
            "## 4. Developer Experience Tips\n\n"
            "- Use `/side` for off-thread questions\n"
            "- Double-tap ESC to rewind when the agent goes off-track\n"
            "- Run `/status` regularly to check model, mode, and context usage\n"
            "- Trigger skills with `$` instead of slash commands\n\n"
            "## 5. Sample Production Config\n\n"
            "```toml\n[agents]\nmax_depth = 1\nmax_threads = 12\n\n"
            "[features]\njs_repl = true\nmulti_agent = true\n"
            "prevent_idle_sleep = true\nmemories = true\ngoals = true\nhooks = true\n\n"
            "[memories]\ngenerate_memories = true\nuse_memories = true\n```\n\n"
            "---\n\n"
            "## The Bottom Line\n\n"
            "Resilient agent workflows aren't about finding the perfect configuration. "
            "Start simple, measure what breaks, and add layers as your specific pain points emerge."
        ),
    },
    {
        "id": make_id(),
        "slug": "from-prototype-to-production-ai-integration-patterns",
        "title": "From Prototype to Production: Real-World AI Integration Patterns",
        "author_name": "AI Lab Engineering",
        "status": "published",
        "published_at": datetime(2026, 6, 5, 10, 0, 0, tzinfo=timezone.utc),
        "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=1200&q=80",
        "excerpt": "Lessons learned from integrating AI into real products -- from batch scoring pipelines to human-in-the-loop review systems. Practical patterns that bridge the gap between demos and production.",
        "content_markdown": (
            "## The Gap Between Demo and Production\n\n"
            "Everyone has seen the impressive AI demo that never made it to production. "
            "The gap is real: a notebook that works on a curated dataset is different from "
            "a pipeline that processes real user data reliably, cost-effectively, and with safeguards.\n\n"
            "---\n\n"
            "## Pattern 1: The Human-in-the-Loop Gate\n\n"
            "The most successful AI integrations are not fully autonomous. "
            "They use **human review at key decision points**.\n\n"
            "![Human in the loop](https://images.unsplash.com/photo-1553877522-43269d4ea984?w=800&q=80)\n\n"
            "### How It Works\n\n"
            "```\nAI Generation -> Human Review -> Approval -> Publication\n"
            "     ^                                    |\n"
            "     +---------- Reject/Revise -----------+\n```\n\n"
            "Each gate has a clear owner and purpose.\n\n"
            "### Why It Works\n\n"
            "- **Accuracy** -- humans catch errors that LLMs confidently produce\n"
            "- **Accountability** -- someone owns every published output\n"
            "- **Improvement** -- rejection feedback trains better prompts\n\n"
            "## Pattern 2: Batch Scoring Pipelines\n\n"
            "For tasks that don't need real-time responses, batch processing is more cost-effective.\n\n"
            "```\nScheduled Trigger -> Queue -> Worker Pool -> Results DB\n"
            "                              |\n"
            "                       LLM API (async)\n```\n\n"
            "**Benefits:** Predictable cost, retry resilience, full observability.\n\n"
            "## Pattern 3: Embeddings for Search and Discovery\n\n"
            "Vector embeddings unlock semantic search without expensive fine-tuning.\n\n"
            "![Embeddings](https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=800&q=80)\n\n"
            "### The Pipeline\n\n"
            "1. Generate embeddings when documents are created\n"
            "2. Store in a vector database (pgvector, Pinecone)\n"
            "3. Query by embedding the search and finding nearest neighbors\n"
            "4. Rank results using hybrid search (vector + keyword)\n\n"
            "## Pattern 4: The Observation Layer\n\n"
            "AI features in production need observability beyond traditional metrics.\n\n"
            "| Metric | Why |\n|--------|-----|\n"
            "| Token usage per stage | Cost attribution |\n"
            "| Generation latency (p50/p95) | User experience |\n"
            "| Human review acceptance rate | Quality signal |\n"
            "| Regeneration rate | Prompt tuning insight |\n\n"
            "## Pattern 5: Gradual Rollout\n\n"
            "Never switch from manual to fully AI-powered in one step:\n\n"
            "1. **Shadow mode** -- AI runs alongside human workflow, logged but unused\n"
            "2. **Assist mode** -- AI suggests, human decides\n"
            "3. **Approve mode** -- AI generates, human reviews\n"
            "4. **Trust mode** -- AI acts autonomously within boundaries\n\n"
            "---\n\n"
            "## The Common Thread\n\n"
            "AI **augments** human judgment, it does not replace it. "
            "The most successful integrations have clear, observable, and adjustable "
            "boundaries between human and machine."
        ),
    },
    {
        "id": make_id(),
        "slug": "human-in-the-loop-advantage-shipping-ai-features",
        "title": "The Human-in-the-Loop Advantage: Shipping AI Features That Actually Work",
        "author_name": "AI Lab Engineering",
        "status": "published",
        "published_at": datetime(2026, 6, 7, 10, 0, 0, tzinfo=timezone.utc),
        "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=1200&q=80",
        "excerpt": "Why human review gates are the secret weapon for production AI -- practical lessons from building a semi-automated content pipeline with quality, safety, and accountability baked in.",
        "content_markdown": (
            "## The Automation Trap\n\n"
            "It is tempting to aim for full automation. In practice, this approach fails "
            "for any task where quality and accuracy matter. The alternative is "
            "**human-in-the-loop (HITL)** -- AI handles generation while humans make critical decisions.\n\n"
            "![AI pipeline](https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80)\n\n"
            "---\n\n"
            "## A Real Pipeline: Seven Stages\n\n"
            "### Stage 1: Idea Generation\n\n"
            "The AI analyzes project context and generates a blog idea with target audience, "
            "angle, and supporting claims grounded in the project.\n\n"
            "### Stage 2: Outline\n\n"
            "The AI produces a structured outline. The human reviews before writing begins.\n\n"
            "### Stage 3: Draft\n\n"
            "With the approved outline, the AI writes a full draft. The human reviews for:\n"
            "- Factual accuracy\n"
            "- Tone and voice\n"
            "- Narrative structure\n\n"
            "### Stage 4: Technical Review\n\n"
            "An automated review checks the draft and flags potential issues. "
            "The human decides whether to accept or request changes.\n\n"
            "### Stage 5: Marketing Metadata\n\n"
            "The AI generates SEO title, meta description, and social copy. "
            "The human adjusts for brand voice and keyword strategy.\n\n"
            "### Stage 6: SEO Audit\n\n"
            "An automated SEO audit checks readability, keyword usage, and heading structure. "
            "The human resolves flagged issues.\n\n"
            "### Stage 7: Publish\n\n"
            "With all gates cleared, the content is published. "
            "The human has reviewed every stage that matters.\n\n"
            "## Measuring the Impact\n\n"
            "| Metric | Improvement |\n|--------|-------------|\n"
            "| Content accuracy | Near 100% vs ~80% for fully automated |\n"
            "| Human review time | Reduced from hours to minutes |\n"
            "| Regeneration rate | ~15% on first pass, converging to ~5% |\n"
            "| Publisher confidence | Significantly higher |\n\n"
            "## Building Your Own HITL Pipeline\n\n"
            "1. **Define Gates** -- Which steps must have human review?\n"
            "2. **Implement the Loop** -- Generate, Review, Approve/Reject, Feedback\n"
            "3. **Measure and Iterate** -- Track pass rates, review times, and costs\n\n"
            "---\n\n"
            "## The Bottom Line\n\n"
            "Human-in-the-loop is not a compromise -- it is a **strategic advantage**. "
            "AI handles the heavy lifting of generation. Humans handle the judgment calls "
            "that require context, taste, and accountability. "
            "The result is a system that scales production without scaling risk."
        ),
    },
]

with engine.begin() as conn:
    for post in BLOG_POSTS:
        conn.execute(
            sa.text(
                """
                INSERT INTO blog_posts (id, slug, title, author_name, status, published_at,
                                        image_url, excerpt, content_markdown)
                VALUES (:id, :slug, :title, :author_name, :status, :published_at,
                        :image_url, :excerpt, :content_markdown)
            """
            ),
            post,
        )
        print(f"  Created: {post['title']}")

print()
print("All 4 blog posts created successfully!")
