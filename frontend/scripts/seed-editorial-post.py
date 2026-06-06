"""
Seed a real editorial blog post directly into the database.
Run: python scripts/seed-editorial-post.py
"""

import sys
import os
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv(
    "AI_LAB_DATABASE_URL",
    "postgresql+psycopg://ai_lab:ai_lab_dev_password@localhost:15432/ai_lab_portal",
)

POST = {
    "title": "Building Your First MCP Server for Codex CLI",
    "slug": "building-first-mcp-server-codex-cli",
    "excerpt": "A step-by-step guide to creating a custom MCP server that extends Codex CLI with your own tools, data sources, and automation workflows.",
    "tags": ["Agent Workflows", "MCP", "Codex CLI"],
    "author_name": "AI Lab",
    "content_markdown": """## Why Build an MCP Server?

The Model Context Protocol (MCP) is the standardised interface that lets AI coding agents like Codex CLI interact with external tools, data sources, and services. While Codex CLI ships with several built-in MCP tools, the real power lies in extending it with your own servers.

A custom MCP server can:

- Query your internal API documentation
- Search your company's knowledge base
- Run custom code analysis on pull requests
- Deploy preview environments on demand
- Interact with your monitoring and alerting systems

In this guide, you will build a practical MCP server that gives Codex CLI the ability to search technical documentation and retrieve code examples from a local registry.

## Prerequisites

Before you start, make sure you have:

- **Node.js 18+** installed (or Python 3.10+ if you prefer Python)
- **Codex CLI** installed and configured
- Basic familiarity with TypeScript or Python

## Understanding the MCP Protocol

MCP follows a client-server architecture:

```
Codex CLI (Host)  <-->  MCP Client  <-->  MCP Server  <-->  External Service
```

The host (Codex CLI) connects to an MCP client which communicates with your MCP server via JSON-RPC over stdio or HTTP. Your server exposes:

- **Tools** -- actions the agent can invoke (e.g. search_docs, get_code_example)
- **Resources** -- data the agent can read (e.g. file contents, API responses)
- **Prompts** -- reusable prompt templates

## Scaffolding the Server

Create a new Node.js project:

```bash
mkdir my-mcp-server
cd my-mcp-server
npm init -y
npm install @modelcontextprotocol/sdk zod
```

Create `src/index.ts` and define your tools with the MCP SDK. The pattern is always the same: define tool schemas with Zod, implement handlers, and connect via StdioServerTransport.

## Registering the Server with Codex CLI

Register your server in the Codex CLI configuration file (`~/.codex/config.json`):

```json
{
  "mcpServers": {
    "docs-registry": {
      "command": "node",
      "args": ["path/to/my-mcp-server/dist/index.js"]
    }
  }
}
```

Restart Codex CLI. The agent can now invoke your custom tools during conversations.

## Testing the Server

Test the server independently before connecting it to Codex:

```bash
npx tsc
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node dist/index.js
```

## Going Further

- Add authentication via environment variables
- Connect to real APIs (Grafana, PagerDuty, CI/CD)
- Add resource templates for knowledge base access
- Support HTTP transport for remote MCP servers
- Add telemetry to track tool usage

## Conclusion

Building an MCP server takes about an hour and unlocks a new level of AI-assisted development. Your Codex CLI agent can now interact with your specific tools and data sources, making it far more useful than a generic coding assistant.

Start with a small, focused server that solves one problem well, then expand as you discover new use cases.
""",
}


def seed_post():
    engine = create_engine(DATABASE_URL)
    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT id FROM blog_posts WHERE slug = :slug"),
            {"slug": POST["slug"]},
        ).fetchone()
        if existing:
            print(f"Post with slug '{POST['slug']}' already exists (id={existing[0]}). Skipping.")
            return

        now = datetime.now(timezone.utc)
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
                "title": POST["title"],
                "slug": POST["slug"],
                "excerpt": POST["excerpt"],
                "content_markdown": POST["content_markdown"],
                "author_name": POST["author_name"],
                "status": "published",
                "published_at": now,
            },
        )
        print(f"Created blog post: {POST['title']} (id={post_id})")

        # Create tags
        for tag_name in POST["tags"]:
            tag_id = str(uuid.uuid4())
            tag_slug = tag_name.lower().replace(" ", "-")
            # Upsert tag
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

            # Link tag to post
            conn.execute(
                text("""
                    INSERT INTO blog_post_tags (post_id, tag_id)
                    VALUES (:post_id, :tag_id)
                    ON CONFLICT DO NOTHING
                """),
                {"post_id": post_id, "tag_id": resolved_tag_id},
            )
            print(f"  Tag: {tag_name}")

    print("\nDone! Visit /blog/building-first-mcp-server-codex-cli to view.")


if __name__ == "__main__":
    seed_post()
