import { headers } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";
import { Bookmark, ExternalLink } from "lucide-react";

import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicEmptyState } from "@/components/public/public-empty-state";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { listUserBookmarks } from "@/lib/blog/social";
import { auth } from "@/lib/auth/server";
import { cn } from "@/lib/utils";

export const dynamic = "force-dynamic";

function formatDate(dateStr: string) {
  const ms = Date.now() - new Date(dateStr).getTime();
  const days = Math.floor(ms / 86400000);
  if (days < 1) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days} days ago`;
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export default async function BookmarksPage() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/login");

  const bookmarks = await listUserBookmarks(session);

  return (
    <PublicPageShell currentPath="/bookmarks">
      <div className={cn(publicMainWidthClass, "flex flex-col gap-8")}>
        <div className="flex items-start justify-between gap-4">
          <PublicBackLink href="/blog">Blog</PublicBackLink>
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Bookmarks</h1>
          <p className="text-sm text-muted-foreground">
            {bookmarks.length} saved {bookmarks.length === 1 ? "post" : "posts"}
          </p>
        </div>

        {bookmarks.length === 0 ? (
          <PublicEmptyState
            description="Bookmark blog posts to read later — click the bookmark icon on any post."
            icon={<Bookmark className="size-5" aria-hidden />}
            title="No bookmarks yet"
          />
        ) : (
          <div className="flex flex-col divide-y divide-border rounded-xl border bg-card">
            {bookmarks.map((bm) => (
              <Link
                key={bm.id}
                href={`/blog/${bm.slug}`}
                className="flex items-center justify-between px-4 py-3.5 transition-colors hover:bg-muted/50"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{bm.title || bm.slug}</p>
                  <p className="text-xs text-muted-foreground">
                    Saved {formatDate(bm.created_at)} · /blog/{bm.slug}
                  </p>
                </div>
                <ExternalLink className="ml-3 size-4 shrink-0 text-muted-foreground" />
              </Link>
            ))}
          </div>
        )}
      </div>
    </PublicPageShell>
  );
}
