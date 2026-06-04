export type ProjectSummary = {
  slug: string;
  title: string;
  description: string;
  publishedAt: string;
  imageUrl?: string | null;
};

export type ProjectDetail = ProjectSummary & {
  id: string;
  contentMarkdown: string;
};

type ApiProjectSummary = {
  slug: string;
  title: string;
  description: string;
  published_at: string;
  image_url?: string | null;
};

type ApiProjectDetail = ApiProjectSummary & {
  id: string;
  content_markdown: string;
};

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

function toSummary(item: ApiProjectSummary): ProjectSummary {
  return {
    slug: item.slug,
    title: item.title,
    description: item.description,
    publishedAt: item.published_at,
    imageUrl: item.image_url,
  };
}

function toDetail(item: ApiProjectDetail): ProjectDetail {
  return {
    ...toSummary(item),
    id: item.id,
    contentMarkdown: item.content_markdown,
  };
}

export async function listPublishedProjects(): Promise<ProjectSummary[]> {
  const response = await fetch(`${backendBaseUrl}/public/projects`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Failed to fetch published projects: ${response.status}`);
  }

  const items = (await response.json()) as ApiProjectSummary[];
  return items.map(toSummary);
}

export async function getPublishedProject(
  slug: string,
): Promise<ProjectDetail | undefined> {
  const response = await fetch(`${backendBaseUrl}/public/projects/${slug}`, {
    cache: "no-store",
  });

  if (response.status === 404) {
    return undefined;
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch published project: ${response.status}`);
  }

  return toDetail((await response.json()) as ApiProjectDetail);
}
