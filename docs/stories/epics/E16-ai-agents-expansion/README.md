# E16 AI Agents Expansion

Extend the AI Lab Portal with three new AI agents that enhance the content lifecycle: repurpose published content for social media, auto-schedule posts for optimal timing, and auto-optimize SEO based on audit results.

## Motivation

The portal already has a robust AI Blog Agent pipeline (idea → outline → draft → review → marketing → SEO → claims → publish). Now we extend the AI capabilities beyond the core pipeline:

1. **Content Repurposing** — Maximize reach by transforming blog posts into social media content
2. **Auto-Scheduling** — Optimize publishing timing using data-driven insights
3. **SEO Auto-Optimize** — Close the loop between SEO audit and content improvement

## Stories

| Story | Scope | Depends On |
|---|---|---|
| **US-107** | Content Repurposing Agent: blog → Twitter thread + LinkedIn article + summary | Existing LLM service |
| **US-108** | Auto-Scheduling Agent: content readiness + calendar + optimal timing | US-103/104 (engagement data) |
| **US-109** | SEO Auto-Optimize Agent: apply audit recommendations to draft content | Existing SEO audit step |

## Design Principles

1. **Human-in-the-loop**: All agent outputs require admin review before action
2. **Fake-first**: Each agent has a fake provider for testing, matching the existing pattern
3. **LLM backend agnostic**: Use `LLMService` ABC — works with both `OpenAILLMService` and `AgentsSDKLLMService`
4. **No auto-posting**: Social media content is copy-paste only (no API keys for Twitter/LinkedIn)
5. **Reuse existing infrastructure**: Prompt registry, fake responses, generation job polling

## Architecture

```text
US-107: Content Repurposing
  Publish → "Repurpose" button → LLMService.generate()
    → Twitter thread format
    → LinkedIn article format
    → Summary snippets
    → Admin review → Copy / Share buttons

US-108: Auto-Scheduling
  Approve publish → Scheduling Agent →
    [Content readiness check]
    [Calendar analysis]
    [Historical engagement (from US-103/104)]
    → Suggested date/time → Admin confirm → Celery scheduled publish

US-109: SEO Auto-Optimize
  SEO audit complete → "Auto-optimize" button →
    [Analyze audit recommendations]
    [Generate improved: title, meta, headings, links]
    → Before/after diff → Admin accept per section → Apply to draft
```

## Exit Criteria

- [x] Content Repurposing Agent generates Twitter threads + LinkedIn articles + summaries
- [ ] Auto-Scheduling Agent suggests optimal publish times with rationale
- [ ] SEO Auto-Optimize Agent produces reviewable before/after diffs
- [ ] All agents have fake providers for E2E testing
- [ ] All agents respect `AI_LAB_LLM_BACKEND` setting
