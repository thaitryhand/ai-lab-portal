"use client";

import { motion } from "framer-motion";
import { Briefcase, Clock, Edit3, ExternalLink, Globe } from "lucide-react";

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
import type { AdminProject } from "./page";

function formatPublishedDate(publishedAt: string | null) {
  if (!publishedAt) return null;
  return new Date(publishedAt).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

type Props = {
  items: AdminProject[];
  publishAction: (formData: FormData) => Promise<void>;
  unpublishAction: (formData: FormData) => Promise<void>;
};

export function ProjectCardList({ items, publishAction, unpublishAction }: Props) {
  if (items.length === 0) {
    return (
      <AdminEmptyState
        ctaHref="/admin/projects/editor"
        ctaLabel="New project"
        description="Create your first project draft to showcase company work."
        icon={<Briefcase className="size-6" aria-hidden />}
        title="No projects yet"
      />
    );
  }

  return (
    <motion.ul
      variants={adminListMotion.container}
      initial="hidden"
      animate="show"
      className={adminListPanelClass}
    >
      {items.map((item) => {
        const publishedLabel = formatPublishedDate(item.published_at);

        return (
          <AdminContentRow
            key={item.id}
            meta={
              <div className="flex flex-wrap items-center gap-2">
                <AdminStatusBadge status={item.status} />
                {publishedLabel ? (
                  <span className="text-[11px] text-muted-foreground">Published {publishedLabel}</span>
                ) : null}
              </div>
            }
            title={
              <h2 className="text-lg font-semibold leading-snug tracking-[-0.02em] text-foreground">
                {item.title}
              </h2>
            }
            actions={
              <AdminListActions>
                <AdminListActionLink href={`/admin/projects/${item.id}/edit`}>
                  <Edit3 className="size-3.5" aria-hidden />
                  Edit
                </AdminListActionLink>

                <AdminListActionForm
                  action={item.status === "published" ? unpublishAction : publishAction}
                >
                  <input name="projectId" type="hidden" value={item.id} />
                  <AdminListSubmitButton
                    variant={item.status === "published" ? "outline" : "secondary"}
                  >
                    {item.status === "published" ? (
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

                {item.status === "published" ? (
                  <AdminListActionLink
                    href={`/projects/${item.slug}`}
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
            <p className="text-sm text-muted-foreground">/{item.slug}</p>
          </AdminContentRow>
        );
      })}
    </motion.ul>
  );
}
