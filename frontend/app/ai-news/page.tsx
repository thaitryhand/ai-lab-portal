import Link from "next/link";
import { Suspense } from "react";

import { PublicIndexEntry } from "@/components/public/public-index-entry";
import { PublicIndexList } from "@/components/public/public-index-list";
import { PublicPageHero } from "@/components/public/public-page-hero";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { SearchInput } from "@/components/public/search-input";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { listPublishedAiNews } from "@/lib/ai-news/posts";
import { createPublicMetadata } from "@/lib/seo/metadata";
import { cn } from "@/lib/utils";

export const metadata = createPublicMetadata({
  title: "AI News | AI Lab Portal",
  description: "Human-reviewed AI news curated from official sources.",
  path: "/ai-news",
});

export const dynamic = "force-dynamic";

const topicFilters = [
  { label: "All", value: undefined },
  { label: "Models", value: "models" },
  { label: "Agents", value: "agents" },
  { label: "Research", value: "research" },
  { label: "Policy", value: "policy" },
  { label: "Infrastructure", value: "infrastructure" },
  { label: "Product", value: "product" },
  { label: "General", value: "general" },
];

export default async function AiNewsIndexPage({
  searchParams,
}: {
  searchParams: Promise<{ topic?: string; q?: string }>;
}) {
  const query = await searchParams;
  const selectedTopic = topicFilters.some((filter) => filter.value === query.topic) ? query.topic : undefined;
  const searchQuery = query.q;
  const items = await listPublishedAiNews(selectedTopic, searchQuery);

  return (
    <PublicPageShell currentPath="/ai-news">
      <section className={cn(publicMainWidthClass, "flex flex-col gap-14 sm:gap-16 lg:gap-20")}>
        <PublicPageHero
          description="Curated AI news from official sources. Items are extracted, deduplicated, scored, and reviewed before publish."
          eyebrow="AI News"
          title="Human-reviewed AI intelligence."
        />

        <div className="-mt-8 flex flex-col gap-6">
          <Suspense fallback={<div className="h-10 w-full max-w-md" />}>
            <SearchInput placeholder="Search AI news…" />
          </Suspense>
          <p className="text-sm text-muted-foreground">
            Have a link worth reviewing?{" "}
            <Link className="underline underline-offset-4" href="/ai-news/submit">
              Submit AI news
            </Link>
            .
          </p>

          <nav aria-label="AI news topics" className="flex flex-wrap gap-2">
            {topicFilters.map((filter) => {
              const isSelected = selectedTopic === filter.value;
              return (
                <Link
                  key={filter.label}
                  aria-current={isSelected ? "page" : undefined}
                  className={cn(
                    "rounded-full border px-3.5 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition-colors",
                    isSelected
                      ? "border-brand/40 bg-brand/10 text-brand"
                      : "border-border/80 text-muted-foreground hover:border-brand/30 hover:text-foreground",
                  )}
                  href={filter.value ? `/ai-news?topic=${filter.value}` : "/ai-news"}
                >
                  {filter.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <PublicIndexList
          emptyDescription={
            selectedTopic
              ? "No published AI news matches this topic yet. Try another topic or clear the filter."
              : "Published AI news will appear here after an editor approves and publishes a candidate."
          }
          emptyTitle={selectedTopic ? "No AI news for this topic" : "No published AI news yet"}
          isEmpty={items.length === 0}
        >
          {items.map((item) => (
            <PublicIndexEntry
              key={item.slug}
              excerpt={item.summary}
              href={`/ai-news/${item.slug}`}
              meta={
                <>
                  {item.sourceName} · {item.topic} · {new Date(item.publishedAt).toLocaleDateString("en-US")}
                </>
              }
              title={item.title}
            />
          ))}
        </PublicIndexList>
      </section>
    </PublicPageShell>
  );
}
