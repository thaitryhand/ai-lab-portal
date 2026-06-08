"""Create a Codex CLI tips blog post."""

import uuid
from datetime import datetime, timezone
import sqlalchemy as sa

from backend.app.database import create_database_engine
from backend.app.settings import Settings

s = Settings(
    database_url="postgresql+psycopg://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal"
)
engine = create_database_engine(s)

post_id = "post_" + uuid.uuid4().hex[:30]

content = """\
## Why Codex CLI Tips Matter

Codex CLI is a powerful agentic coding tool, but its default configuration only scratches the surface. After extensive use across projects of varying complexity, here are the tips that have the highest impact on session longevity, output quality, and workflow control.

---

## 1. Drop /fast for Complex Tasks

Fast mode is excellent for quick iterations — a simple refactor, a quick search, a one-line fix. But for tasks involving many tool calls or deep reasoning, turn it off:

```
/fast off
```

The difference in long sessions is noticeable: the agent takes more time to reason but produces significantly more coherent results, especially when navigating unfamiliar codebases or making architectural decisions.

## 2. Use /side for Off-Thread Questions

When deep in a main task and a related question comes up — "what does this function do?" or "how is this configured?" — use `/side` instead of derailing the main context. It opens a separate conversation thread that doesn't pollute the parent transcript. Think of it as a quick async aside that returns results without context bloat.

## 3. ESC+ESC to Rewind

Double-tapping ESC rewinds the agent to the previous step. When the agent goes in the wrong direction, this is faster than typing a correction — rewind and re-steer the prompt. It is the closest thing to a "undo" button for agent conversations.

## 4. Trigger Skills with $

Use `$skill-name` instead of slash commands for workflow-specific capabilities. This keeps session control commands (`/model`, `/fast`, `/agent`, `/status`) separate from task-specific skills. The `$` prefix is convention for "this does work" while `/` is "this controls the session."

## 5. Enable Memories for Long-Term Context

Memories let Codex retain context across sessions. Enable both the feature and memory behavior:

```toml
# ~/.codex/config.toml
[features]
memories = true

[memories]
generate_memories = true
use_memories = true
```

Memories excel at storing:
- **Project conventions** — lint rules, test patterns, preferred library choices
- **User preferences** — how you like code organized, what you want documented
- **Lessons learned** — anti-patterns discovered, architectural decisions

> Note: memories complement reading the current source. They are not a replacement for understanding the codebase.

## 6. Multi-Agent Architecture

Codex supports running multiple agents in parallel sessions across different threads:

```toml
[agents]
max_depth = 1
max_threads = 12
```

- **`max_threads`** — how many agent sessions can run simultaneously (spawn more agents for parallel work)
- **`max_depth`** — how deep agents can recursively spawn sub-agents

Use `/agent` to switch between active agent threads. Each thread is independent, making this ideal for reviewing multiple files in parallel or running research alongside implementation.

## 7. Codex as an MCP Server

Codex CLI can run as an MCP server, meaning you can embed it into other agent workflows. This is useful when you want a deterministic pipeline where one agent calls Codex via MCP to start or continue a conversation.

## 8. Hooks for Lifecycle Automation

Hooks provide lifecycle callbacks that fire at specific points during agent execution:

| Hook | Trigger | Use Case |
|------|---------|----------|
| `pre_tool` | Before a tool call | Validate inputs, enforce policies |
| `post_tool` | After a tool call | Capture outputs for audit |
| `pre_llm` | Before LLM call | Inject project-specific context |
| `post_llm` | After LLM call | Validate response format |

Enable hooks:
```toml
[features]
hooks = true
```

## 9. Enable JS REPL for Data Work

The built-in JavaScript REPL is excellent for batching tool outputs, parsing JSON, transforming CSV data, or performing quick calculations:

```toml
[features]
js_repl = true
```

Useful for:
- Aggregating multiple tool outputs into a single summary
- Filtering and sorting data before presenting to the agent
- Formatting payloads before passing to APIs

## 10. Use /goal with Caution

`/goal` lets Codex hold a long-term objective across a thread. It is powerful but token-intensive. Official docs mark it as experimental. Use it for well-defined, stable objectives — not for exploratory work where requirements may shift.

```toml
[features]
goals = true
```

---

## Bonus Tips

| Tip | Why |
|-----|-----|
| **`/compact`** after each milestone | Keeps context focused on current task |
| **`/status`** regularly | Check model, mode, permissions, token usage |
| **`/diff`** before asking for changes | See exact current blast radius |
| **`/mcp verbose`** to verify tools | Config existing != runtime available |
| **Set persistent config in `~/.codex/config.toml`** | Repo-specific in `.codex/config.toml` |

---

## Sample Production Config

```toml
[agents]
max_depth = 1
max_threads = 12

[features]
js_repl = true
multi_agent = true
prevent_idle_sleep = true
memories = true
goals = true
hooks = true

[memories]
generate_memories = true
use_memories = true
```

Run `codex feature list` to see all available features.

---

## The Principle

Each tip addresses a specific failure mode: context bloat, wrong direction, unclear state, or lost knowledge. Start with the basics (`/compact`, `/status`), add memories and hooks for long-running projects, and graduate to multi-agent setups when coordinating complex work.
"""

with engine.begin() as conn:
    conn.execute(
        sa.text(
            """INSERT INTO blog_posts (id, slug, title, author_name, status, published_at,
                                       image_url, excerpt, content_markdown)
               VALUES (:id, :slug, :title, :author_name, :status, :published_at,
                       :image_url, :excerpt, :content_markdown)"""
        ),
        {
            "id": post_id,
            "slug": "codex-cli-tips-tricks-production-workflows",
            "title": "Codex CLI Tips and Tricks for Production Workflows",
            "author_name": "AI Lab Engineering",
            "status": "published",
            "published_at": datetime(2026, 6, 8, 10, 0, 0, tzinfo=timezone.utc),
            "image_url": "https://images.unsplash.com/photo-1629654297299-c8506221ca97?w=1200&q=80",
            "excerpt": "Ten practical tips for getting the most out of Codex CLI — from context management and multi-agent setups to hooks, memories, JS REPL, and the hidden configuration flags that make a difference in long-running sessions.",
            "content_markdown": content,
        },
    )
    print("Created: Codex CLI Tips and Tricks for Production Workflows")

# Verify
with engine.connect() as conn:
    row = conn.execute(
        sa.text("SELECT title, slug FROM blog_posts WHERE slug = 'codex-cli-tips-tricks-production-workflows'")
    ).one()
    print(f"Slug: /blog/{row.slug}")
    count = conn.execute(sa.text("SELECT COUNT(*) FROM blog_posts WHERE status='published'")).scalar()
    print(f"Total published posts: {count}")
