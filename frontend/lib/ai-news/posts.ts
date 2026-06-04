export type AiNewsSummary = {
  slug: string;
  title: string;
  summary: string;
  whyItMatters: string;
  sourceName: string;
  topic: string;
  publishedAt: string;
};

export type AiNewsDetail = AiNewsSummary & {
  contentMarkdown: string;
  sourceUrl: string;
  siteName: string | null;
  author: string | null;
};

type ApiAiNewsSummary = {
  slug: string;
  title: string;
  summary: string;
  why_it_matters: string;
  source_name: string;
  topic: string;
  published_at: string;
};

type ApiAiNewsDetail = ApiAiNewsSummary & {
  content_markdown: string;
  source_url: string;
  site_name: string | null;
  author: string | null;
};

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

function toSummary(item: ApiAiNewsSummary): AiNewsSummary {
  return {
    slug: item.slug,
    title: item.title,
    summary: item.summary,
    whyItMatters: item.why_it_matters,
    sourceName: item.source_name,
    topic: item.topic,
    publishedAt: item.published_at,
  };
}

function toDetail(item: ApiAiNewsDetail): AiNewsDetail {
  return {
    ...toSummary(item),
    contentMarkdown: item.content_markdown,
    sourceUrl: item.source_url,
    siteName: item.site_name,
    author: item.author,
  };
}

export async function listPublishedAiNews(topic?: string): Promise<AiNewsSummary[]> {
  const url = new URL("/public/ai-news", backendBaseUrl);
  if (topic) {
    url.searchParams.set("topic", topic);
  }

  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Failed to fetch published AI news: ${response.status}`);
  }

  const items = (await response.json()) as ApiAiNewsSummary[];
  return items.map(toSummary);
}

export async function getPublishedAiNewsItem(slug: string): Promise<AiNewsDetail | undefined> {
  const response = await fetch(`${backendBaseUrl}/public/ai-news/${slug}`, { cache: "no-store" });

  if (response.status === 404) {
    return undefined;
  }

  if (!response.ok) {
    throw new Error(`Failed to fetch published AI news item: ${response.status}`);
  }

  return toDetail((await response.json()) as ApiAiNewsDetail);
}
