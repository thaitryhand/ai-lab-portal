# Overview

## Current Behavior

Knowledge collection exists as a backend service (`KnowledgeService`) that silently
enriches LLM prompts with context from projects, blog posts, showcases, and news.
It's wired into streaming routes and Celery tasks but has:

- Zero tests
- No visible pipeline step in the admin UI
- No persistent storage of collected context
- No way for admin operators to review or edit context before generation
- No agent-based orchestration (synchronous service calls only)

## Target Behavior

Knowledge Collection becomes a visible, agent-driven pipeline stage:

1. **Pipeline step** — "Collect Context" step in the blog-ideas pipeline stepper,
   between idea creation and outline generation.
2. **Admin review UI** — operators can view collected context (project data, related
   posts, news) before approving it for generation.
3. **Persistent storage** — `knowledge_contexts` table stores the collected context
   per idea, enabling audit, reuse, and review.
4. **Tests** — full test coverage for KnowledgeService and the new endpoints.
5. **Agent integration** — optional Agents SDK agent with MCP tools for dynamic
   collection orchestration.

## Affected Users

- **Admin operators** — can review/edit knowledge context before AI generation.
- **AI Blog pipeline** — receives richer, validated context for each stage.

## Affected Product Docs

- `docs/product/blog-agent.md` — update workflow to include Knowledge Collection step.

## Non-Goals

- Multi-turn conversation with the Knowledge Agent (synchronous collection only).
- External document ingestion beyond database sources (no PDF, web crawl, or Slack).
- Auto-approve of collected context (human always reviews).
