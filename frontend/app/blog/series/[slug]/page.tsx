import { headers } from "next/headers";
import Link from "next/link";
import { notFound } from "next/navigation";
import { BookOpen, ChevronLeft } from "lucide-react";

import { PublicPageShell } from "@/components/public/public-page-shell";
import { PublicProse } from "@/components/public/public-prose";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type SeriesPost = {
  part_number: number;
  post_id: string;
  post_title: string;
  post_slug: string;
};

type BlogSeriesDetail = {
  id: string;
  title: string;
  description: string | null;
  slug: string;
  cover_image_url: string | null;
  posts: SeriesPost[];
};

async function fetchSeries(slug: string): Promise<BlogSeriesDetail | null> {
  try {
    const res = await fetch(`${backendBaseUrl}/public/blog-series/${slug}`, {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function BlogSeriesPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const series = await fetchSeries(slug);
  if (!series) notFound();

  const sortedPosts = [...(series.posts || [])].sort(
    (a, b) => a.part_number - b.part_number,
  );

  return (
    <PublicPageShell>
      <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
        <Link
          href="/blog"
          className="mb-6 flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4" />
          Back to blog
        </Link>

        <div className="mb-8 flex items-center gap-3">
          <BookOpen className="h-6 w-6 text-brand" />
          <div>
            <h1 className="font-[family-name:var(--font-gt-super)] text-2xl font-normal tracking-[-0.03em]">
              {series.title}
            </h1>
            {series.description && (
              <p className="mt-1 text-sm text-muted-foreground">{series.description}</p>
            )}
          </div>
        </div>

        <div className="space-y-2">
          {sortedPosts.length === 0 && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No posts in this series yet.
            </p>
          )}
          {sortedPosts.map((post) => (
            <Link
              key={post.post_id}
              href={`/blog/${post.post_slug}`}
              className="flex items-center gap-4 rounded-lg border p-4 transition-colors hover:bg-muted/50"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand/10 text-xs font-bold text-brand">
                {post.part_number}
              </span>
              <span className="font-medium">{post.post_title}</span>
            </Link>
          ))}
        </div>
      </div>
    </PublicPageShell>
  );
}
