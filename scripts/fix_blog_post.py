"""Fix the Codex-tips blog post to be about Pi composition instead."""

import sqlalchemy as sa

from backend.app.database import create_database_engine
from backend.app.settings import Settings

s = Settings(
    database_url="postgresql+psycopg://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal"
)
engine = create_database_engine(s)

new_content = """\
## Composing Pi Extensions for Real Workflows

Individual Pi packages are useful on their own, but their real power comes from **composing them** into integrated workflows. This article walks through practical combinations that solve real problems.

---

## 1. Subagents + Tasks = Parallel Pipeline

Combining **`pi-subagents`** with **`pi-tasks`** creates a structured parallel execution system:

```
Main Agent
  +-- Subagent 1: Research
  |     +-- Task: Find API docs
  |     +-- Task: Read source files
  |     +-- Task: Summarize findings
  +-- Subagent 2: Prototype
  |     +-- Task: Write skeleton code
  |     +-- Task: Add tests
  +-- Subagent 3: Review
        +-- Task: Check code quality
        +-- Task: Verify tests pass
```

Pi-tasks provides visibility into what each subagent is doing. When a task blocks, you see exactly where. When all tasks complete, the main agent has a complete picture.

Install both:
```
npm install @tintinweb/pi-subagents @tintinweb/pi-tasks
```

## 2. Memory + MCP = Persistent Context

**`pi-memory-md`** stores project knowledge as Markdown files. **`pi-mcp-adapter`** connects Pi to external tools. Together, they create a persistent, connected workspace.

### Typical Setup

```
Pi Session
  +-- pi-memory-md
  |     +-- project-conventions.md
  |     +-- lessons-learned.md
  |     +-- api-refs.md
  +-- pi-mcp-adapter
        +-- PostgreSQL MCP (query database)
        +-- Playwright MCP (browser tests)
        +-- GitHub MCP (issues, PRs)
```

Memory files survive across Pi sessions. When starting a new project, Pi reads conventions from memory. When it needs data, it queries through MCP. No manual context re-injection required.

```
npm install pi-memory-md pi-mcp-adapter
```

## 3. Guardrails + Tool Display = Safe Operations

**`pi-guardrails`** constrains what Pi can do. **`pi-tool-display`** makes tool calls visible. Together, they give confidence that Pi is operating correctly.

### Guardrail Configuration

```
# .pi/guardrails.json
{
  "rules": [
    {
      "pattern": "WriteFile",
      "allow": ["src/**", "tests/**"],
      "deny": ["node_modules/**", ".git/**"]
    },
    {
      "pattern": "ExecuteCommand",
      "require_approval": ["rm -rf", "git push"]
    }
  ]
}
```

With tool display enabled, every guardrail check is visible in the terminal. You see what was allowed, blocked, or requires approval.

```
npm install @aliou/pi-guardrails pi-tool-display
```

## 4. Multi-pass + Augment = Quality Loops

**`pi-multi-pass`** runs multiple processing passes. **`pi-augment`** adds workflow hooks. This combination is ideal for tasks needing iterative refinement.

### Two-Pass Review Workflow

```
Pass 1: Generate initial output
  +-- pi-augment hook: validate structure
  +-- pi-augment hook: check completeness

Pass 2: Review and polish
  +-- pi-multi-pass: second pass with review context
  +-- pi-augment hook: verify against requirements
  +-- pi-augment hook: final formatting check
```

Each pass adds a layer of quality. Hooks fire automatically.

```
npm install pi-multi-pass pi-augment
```

## 5. Amplike + Agent Modes = Flexible Workflows

**`pi-amplike`** brings Amp-style permissions and session management. **`pi-agent-modes`** adds different operating modes.

### Mode Switching

```
/research   -- exploratory mode, reads only
/write      -- active development, full permissions
/review     -- analysis mode, read + comment only
/debug      -- verbose output, step-by-step
```

Switching modes changes Pi behavior without restarting the session. This is useful when working across different task types in a single project.

## 6. AskUserQuestion + VCC = Smarter Assistance

**`pi-askuserquestion`** lets Pi ask for clarification instead of guessing. **`pi-vcc`** adds version control coordination. When Pi encounters ambiguity, it asks rather than assuming. VCC ensures decisions are tracked and reversible.

## 7. LazyPi -- The Fastest Start

If you want all of this without configuring each package individually, **LazyPi** bundles the most common extensions into a single setup:

```
curl -fsSL https://lazypi.org/install.sh | sh
```

LazyPi includes sensible defaults for subagents, tasks, memory, MCP, and guardrails. Once you outgrow the defaults, customize by installing individual packages.

---

## Composition Patterns Summary

| Goal | Packages |
|------|----------|
| Parallel execution | subagents + tasks |
| Persistent context | memory-md + mcp-adapter |
| Safe operations | guardrails + tool-display |
| Quality refinement | multi-pass + augment |
| Flexible workflows | amplike + agent-modes |
| Smarter interaction | askuserquestion + vcc |
| Quick start | LazyPi (all-in-one) |

---

## The Principle

Pi extensions follow Unix philosophy: **do one thing well**. Each package solves a focused problem. By composing them, you build workflows that are greater than the sum of their parts.
"""

with engine.begin() as conn:
    conn.execute(
        sa.text(
            "UPDATE blog_posts SET content_markdown = :content, title = :title, excerpt = :excerpt "
            "WHERE slug = 'building-resilient-agent-workflows-pi-extensions'"
        ),
        {
            "content": new_content,
            "title": "Composing Pi Extensions: From Individual Packages to Integrated Workflows",
            "excerpt": "Practical patterns for combining Pi coding agent extensions into integrated workflows that solve real development problems.",
        },
    )
    print("Updated post successfully!")

# Verify
with engine.connect() as conn:
    row = conn.execute(
        sa.text("SELECT title, slug FROM blog_posts WHERE slug = 'building-resilient-agent-workflows-pi-extensions'")
    ).one()
    print(f"Title: {row.title}")
    print(f"Slug:  /blog/{row.slug}")
