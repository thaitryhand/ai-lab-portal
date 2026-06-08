# Product

> Synthesized from `docs/product/overview.md` and project context.
> For the full product overview including MVP modules and locked rules, see `docs/product/`.

## Register

product

## Users

**External visitors** — technical decision-makers, engineering leaders, and AI practitioners evaluating the company's AI Lab capability. They land on public pages (blog, showcases, lab, AI news) to assess depth of AI/LLM engineering, read case studies, and determine whether the Lab can solve their problems.

**Internal operators** — content editors, AI agents, and reviewers managing the editorial pipeline via the admin dashboard. They approve/reject blog ideas, review news items, configure sources, and monitor AI generation jobs. Their primary task is keeping credible AI content flowing to the public surface.

## Product Purpose

AI Lab Portal is the public and internal platform for repositioning the company from an IT outsource/offshore development provider into an AI/LLM Lab. The portal must demonstrate real AI product capability, publish credible AI Lab content, and turn market intelligence into sales-ready proof.

The system itself is a showcase: built with AI-native workflows (agent pipelines, structured LLM outputs, Celery orchestration), the platform is its own best credential.

**Three strategic goals:**
1. Build credibility with potential clients by showing practical AI products, AI engineering lessons, and evaluation practices.
2. Create a repeatable content and intelligence engine for sales, marketing, and leadership.
3. Make the system itself explainable as an AI workflow showcase.

## Brand Personality

- **Credible** — expert confidence, not hype. Substance over volume.
- **Editorial** — writing-forward, editorial tone. Medium-inspired warmth.
- **Precise** — clean, intentional, minimal. Every element earns its place.

The voice is that of an engineering team that ships real AI products — knowledgeable, generous with insight, but never selling too hard. The platform should feel like reading a respected engineering blog, not like a marketing site.

### Tone guidance
- Public content: warm, authoritative, accessible to technical readers
- Admin UI: neutral, tool-like, transparent about state and progress
- Never: breathless AI hype, "revolutionary" language, glowing purple gradients, SaaS cliché dashboard aesthetic

## Anti-references

This platform must NOT look like:

- Generic dark AI dashboard with neon accents and glassmorphism
- SaaS landing page with big numbers, gradient text, and stock photos
- Purple/magenta AI gradient as a design crutch
- Heavy shadows, glossy cards, or dense chrome on public pages
- "Built with AI" badge aesthetic — the proof is in the content, not the decoration

## Design Principles

1. **Practice what you preach.** The platform's design quality is a product credential. Sloppy UI undercuts the AI Lab's credibility.
2. **Content first, chrome last.** Public pages serve writing and media. Decoration must never compete with content.
3. **Transparent by default.** Admin workflows expose state, progress, errors, and agent reasoning. No black boxes.
4. **Human-in-the-loop.** Publishing requires human approval. The UI makes approval workflows clear and auditable.
5. **Restrained accent.** A single green accent reserved for emphasis and brand moments. Rarity is the point.

## Accessibility & Inclusion

- WCAG 2.1 AA minimum for all public and admin surfaces.
- Sufficient color contrast on warm vellum backgrounds.
- Reduced motion respected via `prefers-reduced-motion`.
- Keyboard-navigable admin workflows.
- Semantic HTML and ARIA labels throughout.
