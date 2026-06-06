export type BlogIdeaGeneratePayload = {
  project_name: string;
  project_summary: string;
  ai_capabilities: string;
  technical_highlights: string;
  business_value: string;
};

export type ProjectContextDetail = {
  title: string;
  description: string;
  content_markdown: string;
};

export type ShowcaseContextDetail = {
  title: string;
  hero_summary: string;
  industry: string | null;
  use_case: string | null;
  content_markdown: string;
};

const HIGHLIGHT_LIMIT = 2400;

function truncate(text: string, limit = HIGHLIGHT_LIMIT) {
  const trimmed = text.trim();
  if (trimmed.length <= limit) return trimmed;
  return `${trimmed.slice(0, limit).trimEnd()}…`;
}

export function mapProjectToGeneratePayload(
  project: ProjectContextDetail,
): BlogIdeaGeneratePayload {
  return {
    project_name: project.title,
    project_summary: project.description,
    ai_capabilities: "",
    technical_highlights: truncate(project.content_markdown),
    business_value: project.description,
  };
}

export function mapShowcaseToGeneratePayload(
  showcase: ShowcaseContextDetail,
): BlogIdeaGeneratePayload {
  const capabilityParts = [showcase.use_case, showcase.industry].filter(Boolean);
  return {
    project_name: showcase.title,
    project_summary: showcase.hero_summary,
    ai_capabilities: capabilityParts.join(" — "),
    technical_highlights: truncate(showcase.content_markdown),
    business_value: showcase.industry ?? showcase.use_case ?? showcase.hero_summary,
  };
}
