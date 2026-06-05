import type { MetadataRoute } from "next";

const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://ailabportal.com";

// Backend base URL for fetching dynamic data
const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type BlogPost = { slug: string; updated_at: string | null };
type ShowcasePost = { slug: string; updated_at: string | null };
type ProjectPost = { slug: string; updated_at: string | null };
type NewsItem = { slug: string; updated_at: string | null };

async function fetchJson<T>(url: string): Promise<T[]> {
  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return [];
    return (await res.json()) as T[];
  } catch {
    return [];
  }
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // ── Static routes ──────────────────────────────────────────────────────
  const staticRoutes: MetadataRoute.Sitemap = [
    { url: baseUrl, lastModified: new Date(), changeFrequency: "weekly", priority: 1 },
    { url: `${baseUrl}/blog`, lastModified: new Date(), changeFrequency: "daily", priority: 0.9 },
    { url: `${baseUrl}/lab`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.8 },
    { url: `${baseUrl}/showcases`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.7 },
    { url: `${baseUrl}/projects`, lastModified: new Date(), changeFrequency: "weekly", priority: 0.7 },
    { url: `${baseUrl}/ai-news`, lastModified: new Date(), changeFrequency: "daily", priority: 0.8 },
    { url: `${baseUrl}/contact`, lastModified: new Date(), changeFrequency: "monthly", priority: 0.4 },
  ];

  // ── Dynamic blog posts ─────────────────────────────────────────────────
  const blogPosts = await fetchJson<BlogPost>(
    `${backendBaseUrl}/public/blog-posts`,
  );

  for (const post of blogPosts) {
    staticRoutes.push({
      url: `${baseUrl}/blog/${post.slug}`,
      lastModified: post.updated_at ? new Date(post.updated_at) : new Date(),
      changeFrequency: "monthly" as const,
      priority: 0.8,
    });
  }

  // ── Showcases ──────────────────────────────────────────────────────────
  const showcases = await fetchJson<ShowcasePost>(
    `${backendBaseUrl}/public/showcases`,
  );

  for (const s of showcases) {
    staticRoutes.push({
      url: `${baseUrl}/showcases/${s.slug}`,
      lastModified: s.updated_at ? new Date(s.updated_at) : new Date(),
      changeFrequency: "monthly" as const,
      priority: 0.6,
    });
  }

  // ── Projects ───────────────────────────────────────────────────────────
  const projects = await fetchJson<ProjectPost>(
    `${backendBaseUrl}/public/projects`,
  );

  for (const p of projects) {
    staticRoutes.push({
      url: `${baseUrl}/projects/${p.slug}`,
      lastModified: p.updated_at ? new Date(p.updated_at) : new Date(),
      changeFrequency: "monthly" as const,
      priority: 0.6,
    });
  }

  // ── AI News ────────────────────────────────────────────────────────────
  try {
    const newsItems = await fetchJson<NewsItem>(
      `${backendBaseUrl}/public/ai-news`,
    );

    for (const n of newsItems) {
      staticRoutes.push({
        url: `${baseUrl}/ai-news/${n.slug}`,
        lastModified: n.updated_at ? new Date(n.updated_at) : new Date(),
        changeFrequency: "weekly" as const,
        priority: 0.7,
      });
    }
  } catch {
    // news endpoint may not exist
  }

  return staticRoutes;
}
