"use client";

import { motion } from "framer-motion";
import { CheckCircle, ExternalLink, Globe, Newspaper, RotateCcw, XCircle } from "lucide-react";

import { AdminContentRow, adminListMotion } from "@/components/admin/admin-content-row";
import { AdminEmptyState } from "@/components/admin/admin-empty-state";
import {
  AdminListActionForm,
  AdminListActionLink,
  AdminListActions,
  AdminListSubmitButton,
} from "@/components/admin/admin-list-actions";
import { adminListPanelClass } from "@/components/admin/admin-ui";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { AdminNewsReviewItem } from "./page";

type Props = {
  items: AdminNewsReviewItem[];
  approveAction: (formData: FormData) => Promise<void>;
  rejectAction: (formData: FormData) => Promise<void>;
  publishAction: (formData: FormData) => Promise<void>;
  unpublishAction: (formData: FormData) => Promise<void>;
};

const statusTone: Record<AdminNewsReviewItem["review_status"], string> = {
  candidate: "border-amber-500/25 bg-amber-500/10 text-amber-700 dark:text-amber-300",
  approved: "border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
  rejected: "border-destructive/25 bg-destructive/10 text-destructive",
  low_score: "border-muted-foreground/25 bg-muted/40 text-muted-foreground",
  skipped: "border-muted-foreground/25 bg-muted/40 text-muted-foreground",
  published: "border-brand/25 bg-brand/10 text-brand",
};

function formatDate(value: string | null) {
  if (!value) return null;
  return new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function scorePercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function ReviewItemActions({
  item,
  approveAction,
  rejectAction,
  publishAction,
  unpublishAction,
}: Props & { item: AdminNewsReviewItem }) {
  if (item.review_status === "candidate") {
    return (
      <>
        <AdminListActionForm action={approveAction}>
          <input name="reviewId" type="hidden" value={item.id} />
          <AdminListSubmitButton variant="brand">
            <CheckCircle className="size-3.5" aria-hidden />
            Approve
          </AdminListSubmitButton>
        </AdminListActionForm>
        <AdminListActionForm action={rejectAction}>
          <input name="reviewId" type="hidden" value={item.id} />
          <AdminListSubmitButton variant="outline">
            <XCircle className="size-3.5" aria-hidden />
            Reject
          </AdminListSubmitButton>
        </AdminListActionForm>
      </>
    );
  }

  if (item.review_status === "approved") {
    return (
      <AdminListActionForm action={publishAction}>
        <input name="reviewId" type="hidden" value={item.id} />
        <AdminListSubmitButton variant="secondary">
          <Globe className="size-3.5" aria-hidden />
          Publish
        </AdminListSubmitButton>
      </AdminListActionForm>
    );
  }

  if (item.review_status === "published") {
    return (
      <>
        <AdminListActionForm action={unpublishAction}>
          <input name="reviewId" type="hidden" value={item.id} />
          <AdminListSubmitButton variant="outline">
            <RotateCcw className="size-3.5" aria-hidden />
            Unpublish
          </AdminListSubmitButton>
        </AdminListActionForm>
        {item.slug ? (
          <AdminListActionLink href={`/ai-news/${item.slug}`} rel="noopener noreferrer" target="_blank" variant="ghost">
            <ExternalLink className="size-3" aria-hidden />
            View
          </AdminListActionLink>
        ) : null}
      </>
    );
  }

  return null;
}

export function ReviewItemCardList({ items, approveAction, rejectAction, publishAction, unpublishAction }: Props) {
  if (items.length === 0) {
    return (
      <AdminEmptyState
        description="Scored AI News candidates appear here after RSS crawl, extraction, and scoring jobs run."
        icon={<Newspaper className="size-6" aria-hidden />}
        title="No review candidates yet"
      />
    );
  }

  return (
    <motion.ul variants={adminListMotion.container} initial="hidden" animate="show" className={adminListPanelClass}>
      {items.map((item) => {
        const publishedLabel = formatDate(item.published_at);
        return (
          <AdminContentRow
            key={item.id}
            meta={
              <div className="flex flex-wrap items-center gap-2">
                <Badge className={cn("rounded-md font-normal", statusTone[item.review_status])} variant="outline">
                  {item.review_status}
                </Badge>
                <span className="text-[11px] text-muted-foreground">Score {scorePercent(item.final_publish_score)}</span>
                <span className="text-[11px] text-muted-foreground">Source {item.source_id.slice(0, 8)}</span>
                {publishedLabel ? <span className="text-[11px] text-muted-foreground">Published {publishedLabel}</span> : null}
              </div>
            }
            title={<h2 className="text-lg font-semibold leading-snug tracking-[-0.02em] text-foreground">{item.title}</h2>}
            actions={
              <AdminListActions>
                <ReviewItemActions
                  item={item}
                  items={items}
                  approveAction={approveAction}
                  rejectAction={rejectAction}
                  publishAction={publishAction}
                  unpublishAction={unpublishAction}
                />
              </AdminListActions>
            }
          >
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>{item.summary}</p>
              <p>
                <span className="font-medium text-foreground">Why it matters:</span> {item.why_it_matters}
              </p>
              <dl className="grid gap-2 text-xs sm:grid-cols-3">
                <div>
                  <dt className="text-muted-foreground">Relevance</dt>
                  <dd className="font-medium text-foreground">{scorePercent(item.relevance_score)}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Novelty</dt>
                  <dd className="font-medium text-foreground">{scorePercent(item.novelty_score)}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Spam risk</dt>
                  <dd className="font-medium text-foreground">{scorePercent(item.spam_risk_score)}</dd>
                </div>
              </dl>
            </div>
          </AdminContentRow>
        );
      })}
    </motion.ul>
  );
}
