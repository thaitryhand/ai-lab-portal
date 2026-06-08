import type { Metadata } from "next";

import { TourCta } from "@/components/tour/tour-cta";
import { TourExamples } from "@/components/tour/tour-examples";
import type { TourExampleItem } from "@/components/tour/tour-examples";
import { TourHero } from "@/components/tour/tour-hero";
import { TourPipeline } from "@/components/tour/tour-pipeline";
import { TourStats } from "@/components/tour/tour-stats";
import type { TourStatsData } from "@/components/tour/tour-stats";
import { PublicEditorialShell } from "@/components/public/public-editorial-shell";
import { createPublicMetadata } from "@/lib/seo/metadata";

export const metadata: Metadata = createPublicMetadata({
  title: "AI Lab Tour",
  description:
    "See the AI Lab Portal in action — a seven-stage semi-auto pipeline from project to published post.",
  path: "/tour",
});

const BACKEND_URL = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

interface ApiBlogSummary {
  slug: string;
  title: string;
  excerpt: string;
  author_name: string;
  published_at: string;
}

interface ApiShowcaseSummary {
  slug: string;
  title: string;
  hero_summary: string;
  industry: string | null;
  use_case: string | null;
  published_at: string;
}

interface ApiProjectSummary {
  slug: string;
  title: string;
  description: string;
  published_at: string;
}

interface ApiNewsSummary {
  slug: string;
  title: string;
  excerpt: string | null;
}

async function fetchJson<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(3000) });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export default async function TourPage() {
  // Fetch all content in parallel with timeouts
  const [posts, showcases, projects, news] = await Promise.all([
    fetchJson<ApiBlogSummary[]>(`${BACKEND_URL}/public/blog-posts`),
    fetchJson<ApiShowcaseSummary[]>(`${BACKEND_URL}/public/showcases`),
    fetchJson<ApiProjectSummary[]>(`${BACKEND_URL}/public/projects`),
    fetchJson<ApiNewsSummary[]>(`${BACKEND_URL}/public/ai-news`),
  ]);

  // Build stats from real data
  const stats: TourStatsData = {
    blogPosts: posts?.length ?? 6,
    showcases: showcases?.length ?? 3,
    projects: projects?.length ?? 2,
    newsItems: news?.length ?? 12,
  };

  // Build examples from real published content, with fallback
  const examples: TourExampleItem[] = [];

  if (posts) {
    for (const p of posts.slice(0, 3)) {
      examples.push({
        title: p.title,
        category: "Engineering",
        href: `/blog/${p.slug}`,
        excerpt: p.excerpt,
      });
    }
  }

  if (showcases) {
    for (const s of showcases.slice(0, 2)) {
      examples.push({
        title: s.title,
        category: s.industry ?? "Case Study",
        href: `/showcases/${s.slug}`,
        excerpt: s.hero_summary,
      });
    }
  }

  if (projects) {
    for (const p of projects.slice(0, 1)) {
      examples.push({
        title: p.title,
        category: "Project",
        href: `/projects/${p.slug}`,
        excerpt: p.description,
      });
    }
  }

  return (
    <PublicEditorialShell>
      <TourHero />
      <TourPipeline />
      <TourStats data={stats} />
      <TourExamples examples={examples.length > 0 ? examples : undefined} />
      <TourCta />
    </PublicEditorialShell>
  );
}
