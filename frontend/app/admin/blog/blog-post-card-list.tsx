"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Clock, Edit3, ExternalLink, FileText, Globe, Search } from "lucide-react";

import { AdminContentRow, adminListMotion } from "@/components/admin/admin-content-row";
import { AdminEmptyState } from "@/components/admin/admin-empty-state";
import { AdminStatusBadge } from "@/components/admin/admin-status-badge";
import {
  AdminListActionForm,
  AdminListActionLink,
  AdminListActions,
  AdminListSubmitButton,
} from "@/components/admin/admin-list-actions";
import { adminListPanelClass } from "@/components/admin/admin-ui";
import { cn } from "@/lib/utils";
import type { AdminBlogPost } from "./page";

function formatPublishedDate(publishedAt: string | null) {
  if (!publishedAt) return null;
  return new Date(publishedAt).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

type Props = {
  posts: AdminBlogPost[];
  publishAction: (formData: FormData) => Promise<void>;
  unpublishAction: (formData: FormData) => Promise<void>;
};

export function BlogPostCardList({ posts, publishAction, unpublishAction }: Props) {
  const [query, setQuery] = useState("");

  const filtered = query.trim()
    ? posts.filter(
        (p) =>
          p.title.toLowerCase().includes(query.toLowerCase()) ||
          p.slug.toLowerCase().includes(query.toLowerCase()),
      )
    : posts;

  if (posts.length === 0) {
    return (
      <AdminEmptyState
        ctaHref="/admin/blog/editor"
        ctaLabel="New draft"
        description="Create your first draft to start the manual publishing workflow."
        icon={<FileText className="size-6" aria-hidden />}
        title="No blog posts yet"
      />
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Search bar */}
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground/60" />
        <input
          type="search"
          placeholder="Search posts by title or slug…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="h-10 w-full rounded-[var(--radius-admin-sm)] border border-border/60 bg-card pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground/50 focus:border-brand/40 focus:outline-none focus:ring-[3px] focus:ring-brand/10"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-[var(--radius-admin-md)] border border-border/60 bg-card px-6 py-12 text-center">
          <Search className="size-6 text-muted-foreground/40" />
          <p className="text-sm text-muted-foreground">
            No posts match <span className="font-medium text-foreground">&ldquo;{query}&rdquo;</span>
          </p>
        </div>
      ) : (
        <motion.ul
          variants={adminListMotion.container}
          initial="hidden"
          animate="show"
          className={adminListPanelClass}
        >
          {filtered.map((post) => {
            const publishedLabel = formatPublishedDate(post.published_at);

            return (
              <AdminContentRow
                key={post.id}
                meta={
                  <div className="flex flex-wrap items-center gap-2">
                    <AdminStatusBadge status={post.status} />
                    {publishedLabel ? (
                      <span className="text-[11px] text-muted-foreground">Published {publishedLabel}</span>
                    ) : null}
                  </div>
                }
                title={
                  <h2 className="text-lg font-semibold leading-snug tracking-[-0.02em] text-foreground">
                    {post.title}
                  </h2>
                }
                actions={
                  <AdminListActions>
                    <AdminListActionLink href={`/admin/blog/${post.id}/edit`}>
                      <Edit3 className="size-3.5" aria-hidden />
                      Open editor
                    </AdminListActionLink>

                    <AdminListActionForm
                      action={post.status === "published" ? unpublishAction : publishAction}
                    >
                      <input name="postId" type="hidden" value={post.id} />
                      <AdminListSubmitButton
                        variant={post.status === "published" ? "outline" : "secondary"}
                      >
                        {post.status === "published" ? (
                          <>
                            <Clock className="size-3.5" aria-hidden />
                            Unpublish
                          </>
                        ) : (
                          <>
                            <Globe className="size-3.5" aria-hidden />
                            Publish
                          </>
                        )}
                      </AdminListSubmitButton>
                    </AdminListActionForm>

                    {post.status === "published" ? (
                      <AdminListActionLink
                        href={`/blog/${post.slug}`}
                        rel="noopener noreferrer"
                        target="_blank"
                        variant="ghost"
                      >
                        <ExternalLink className="size-3" aria-hidden />
                        View
                      </AdminListActionLink>
                    ) : null}
                  </AdminListActions>
                }
              >
                <p className="text-sm text-muted-foreground">/{post.slug}</p>
              </AdminContentRow>
            );
          })}
        </motion.ul>
      )}

      {query.trim() && (
        <p className="text-[11px] text-muted-foreground/60">
          {filtered.length} of {posts.length} post{posts.length !== 1 ? "s" : ""}
        </p>
      )}
    </div>
  );
}
