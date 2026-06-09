# Design

## Domain Model

```
KnowledgeContext {
    id: str (PK)
    blog_idea_id: str (FK -> blog_ideas.id, unique)
    project_name: str | null
    project_summary: str | null
    project_content: str | null
    related_blog_posts: JSON (list of {title, excerpt, slug})
    related_showcases: JSON (list of {title, summary, slug})
    recent_news: JSON (list of {title, summary})
    raw_collected_at: datetime
    approved_at: datetime | null
    approved_by: str | null
    edited_at: datetime | null
    created_at: datetime
    updated_at: datetime
}
```

## Application Flow

```
Admin opens blog idea detail
  -> Pipeline stepper shows "Collect Context" step (active if idea approved)
  -> Admin clicks "Collect context" button
    -> POST /admin/knowledge/collect {idea_id}
      -> KnowledgeService queries projects, posts, showcases, news
      -> Stores result in knowledge_contexts table
      -> Returns collected context
  -> Admin views collected context in review UI
    -> Can edit project_name, adjust summary
    -> Can see which sources contributed data
  -> Admin clicks "Approve context"
    -> PATCH /admin/knowledge/context/{idea_id}/approve
      -> Sets approved_at, advances pipeline to outline generation
      -> Next outline prompt includes stored context
```

## Interface Contract

### POST /admin/knowledge/collect
- Request: `{ idea_id: string }`
- Response: `KnowledgeContext` (the collected context)
- Errors: 404 if idea not found, 409 if already collected

### GET /admin/knowledge/context/{idea_id}
- Response: `KnowledgeContext | null`
- Admin: returns full context even if not yet approved

### PATCH /admin/knowledge/context/{idea_id}
- Request: partial `KnowledgeContextUpdate` (editable fields)
- Response: updated `KnowledgeContext`

### PATCH /admin/knowledge/context/{idea_id}/approve
- Response: updated `KnowledgeContext` with `approved_at` set

### KnowledgeContextUpdate Pydantic
```python
class KnowledgeContextUpdate(BaseModel):
    project_name: str | None = None
    project_summary: str | None = None
    project_content: str | None = None
```

## Data Model

### Table `knowledge_contexts`

| Column | Type | Constraints |
|--------|------|-------------|
| id | VARCHAR(64) | PK |
| blog_idea_id | VARCHAR(64) | UNIQUE, FK -> blog_ideas(id) ON DELETE CASCADE |
| project_name | VARCHAR(255) | NULL |
| project_summary | TEXT | NULL |
| project_content | TEXT | NULL |
| related_blog_posts | TEXT (JSON) | NULL |
| related_showcases | TEXT (JSON) | NULL |
| recent_news | TEXT (JSON) | NULL |
| raw_collected_at | TIMESTAMPTZ | NOT NULL |
| approved_at | TIMESTAMPTZ | NULL |
| approved_by | VARCHAR(255) | NULL |
| edited_at | TIMESTAMPTZ | NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

Migration: `20260608_0042_knowledge_contexts`
Down revision: depends on current head

## UI / Platform Impact

### Pipeline stepper update

Add a new step "collect" between "idea" and "outline" in the step order:

```
idea -> collect -> outline -> draft -> review -> marketing -> seo -> claims -> publish
```

### PipelineNextActionBanner update

New states for collect step:
- **Ready to collect** — idea approved, no context yet → "Collect context" button
- **Context collected** — context exists but not approved → "Review & approve context" button
- **Context approved** → advance to outline

### Admin context review UI

A new section/card on the blog idea detail page showing:
- Source summary: "Collected from 1 project, 3 blog posts, 2 showcases, 5 news articles"
- Editable project summary field
- Read-only list of related blog posts/showcases (expandable)
- Read-only count of news articles found
- "Edit context" button → inline editing
- "Approve context" button → advances pipeline

## Observability

- `knowledge_contexts` table provides full audit trail (what was collected, when, approved by whom)
- Pipeline next-action resolves "collect" state for the banner
- Collected context stored as JSON for debug/review

## Alternatives Considered

1. **Keep as silent background enrichment** — rejected because operators have no visibility into what context the AI uses, increasing hallucination risk.
2. **Agent-only collection** — rejected for phase 1 to keep scope bounded; agent orchestration can be added later.
3. **Auto-collect on idea creation** — simpler UX but removes human review opportunity.
