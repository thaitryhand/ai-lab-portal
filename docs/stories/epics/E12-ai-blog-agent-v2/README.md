# E12 AI Blog Agent v2

Semi-auto blog agent for admin operators: generate ideas from Project or
Showcase context, approve each pipeline gate, orchestrate next stages, publish
with claim gate.

## Interview decisions (2026-06-06)

| Decision | Choice |
| --- | --- |
| Automation | Semi-auto — human approve each gate; code orchestrator runs next stage |
| Success metric | Quality-first — ≥1 publish/week from week 3, ≤30 min human, claim gate required |
| Context source | Project + Showcase picker; default Project |
| Ownership | Admin-only (`/admin/blog-ideas/*`) |

## Stories

| Story | Title | Status |
| --- | --- | --- |
| US-084 | Generate from context UI | implemented |
| US-085 | Project/showcase picker | implemented |
| US-086 | E2E golden path generate → publish | implemented |
| US-087 | Editorial seed via agent pipeline | implemented |
| US-088 | Pipeline stepper UX | implemented |
| US-089 | Run next stage orchestrator | implemented |
| US-090 | Claim review UI | implemented |

## Non-goals (Phase 1)

- Author self-serve agent
- Full auto publish
- OpenAI Agents SDK migration
