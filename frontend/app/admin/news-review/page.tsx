import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { AdminCmsShell } from "@/components/admin/admin-cms-shell";
import { AdminListToolbar } from "@/components/admin/admin-list-toolbar";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import {
  approveReviewItemAction,
  publishReviewItemAction,
  rejectReviewItemAction,
  unpublishReviewItemAction,
} from "./actions";
import { ReviewItemCardList } from "./review-item-card-list";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

export type AdminNewsReviewItem = {
  id: string;
  extracted_article_id: string;
  raw_item_id: string;
  source_id: string;
  title: string;
  source_credibility_score: number;
  engagement_score: number;
  relevance_score: number;
  novelty_score: number;
  technical_depth_score: number;
  business_value_score: number;
  spam_risk_score: number;
  final_publish_score: number;
  summary: string;
  why_it_matters: string;
  scorer_version: string;
  review_status: "candidate" | "approved" | "rejected" | "low_score" | "skipped" | "published";
  review_notes: string | null;
  scored_at: string;
  reviewed_at: string | null;
  slug: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
};

async function listReviewItems() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}/admin/news/review-items?limit=100`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });

  if (!response.ok) throw new Error(`Failed to fetch AI news review items: ${response.status}`);
  return (await response.json()) as AdminNewsReviewItem[];
}

export default async function AdminNewsReviewPage() {
  const items = await listReviewItems();
  const pendingCount = items.filter((item) => item.review_status === "candidate").length;
  const approvedCount = items.filter((item) => item.review_status === "approved").length;
  const publishedCount = items.filter((item) => item.review_status === "published").length;

  return (
    <AdminCmsShell active="news-review">
      <div className={adminPageStackClass}>
        <AdminListToolbar
          ctaHref="/admin/news-sources"
          ctaLabel="Manage sources"
          description="Review scored AI News candidates, approve high-signal items, and publish them to the public feed."
          eyebrow="AI News"
          metrics={[
            { dotClassName: "bg-amber-500", label: `${pendingCount} candidates` },
            { dotClassName: "bg-emerald-500", label: `${approvedCount} approved` },
            { dotClassName: "bg-brand", label: `${publishedCount} published` },
          ]}
          title="Review queue"
        />
        <ReviewItemCardList
          items={items}
          approveAction={approveReviewItemAction}
          rejectAction={rejectReviewItemAction}
          publishAction={publishReviewItemAction}
          unpublishAction={unpublishReviewItemAction}
        />
      </div>
    </AdminCmsShell>
  );
}
