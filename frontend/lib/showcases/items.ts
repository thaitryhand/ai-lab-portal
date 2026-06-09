export type ShowcaseSummary = {
  slug: string;
  title: string;
  heroSummary: string;
  industry: string | null;
  useCase: string | null;
  publishedAt: string;
  imageUrl?: string | null;
};

export type ShowcaseDetail = ShowcaseSummary & {
  id: string;
  contentMarkdown: string;
};

type ApiShowcaseSummary = {
  slug: string;
  title: string;
  hero_summary: string;
  industry: string | null;
  use_case: string | null;
  published_at: string;
  image_url?: string | null;
};

type ApiShowcaseDetail = ApiShowcaseSummary & {
  id: string;
  content_markdown: string;
};

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

function toSummary(item: ApiShowcaseSummary): ShowcaseSummary {
  return {
    slug: item.slug,
    title: item.title,
    heroSummary: item.hero_summary,
    industry: item.industry,
    useCase: item.use_case,
    publishedAt: item.published_at,
    imageUrl: item.image_url,
  };
}

function toDetail(item: ApiShowcaseDetail): ShowcaseDetail {
  return {
    ...toSummary(item),
    id: item.id,
    contentMarkdown: item.content_markdown,
  };
}

export async function listPublishedShowcases(): Promise<ShowcaseSummary[]> {
  const response = await fetch(`${backendBaseUrl}/public/showcases`);

  if (!response.ok) {
    throw new Error(`Failed to fetch published showcases: ${response.status}`);
  }

  const items = (await response.json()) as ApiShowcaseSummary[];
  return items.map(toSummary);
}

export async function getPublishedShowcase(slug: string): Promise<ShowcaseDetail | undefined> {
  const response = await fetch(`${backendBaseUrl}/public/showcases/${slug}`);

  if (response.status === 404) {
    return undefined;
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch published showcase: ${response.status}`);
  }

  return toDetail((await response.json()) as ApiShowcaseDetail);
}
