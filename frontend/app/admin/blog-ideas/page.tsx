import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { adminPageStackClass } from "@/components/admin/admin-ui";
import { AdminListToolbar } from "@/components/admin/admin-list-toolbar";
import { ButtonLink } from "@/components/ui/button-link";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import {
  approveIdeaAction,
  rejectIdeaAction,
  generateOutlineAction,
  generateDraftAction,
} from "./actions";
import { BlogIdeaCardList } from "./idea-card-list";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

export type BlogIdeaSummary = {
  id: string;
  title: string;
  angle: string;
  source: "manual" | "ai_generated";
  status: "pending" | "approved" | "rejected";
  outline_status: string | null;
  draft_status: string | null;
  created_at: string;
};

async function listBlogIdeas() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}/admin/blog-ideas`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });

  if (!response.ok) return [];
  return (await response.json()) as BlogIdeaSummary[];
}

export default async function AdminBlogIdeasPage() {
  const ideas = await listBlogIdeas();
  const pendingCount = ideas.filter((i) => i.status === "pending").length;
  const approvedCount = ideas.filter((i) => i.status === "approved").length;

  return (
      <div className={adminPageStackClass}>
        <AdminListToolbar
          ctaHref="/admin/blog-ideas/new"
          ctaLabel="Generate idea"
          description="Generate ideas from projects or showcases, then approve and run the outline → draft → review pipeline."
          secondaryAction={
            <ButtonLink href="/admin/blog-ideas/new?mode=manual" variant="outline">
              Manual idea
            </ButtonLink>
          }
          eyebrow="Content pipeline"
          metrics={[
            { dotClassName: "bg-brand", label: `${approvedCount} approved` },
            { dotClassName: "bg-amber-500", label: `${pendingCount} pending` },
            { dotClassName: "bg-muted-foreground", label: `${ideas.length} total` },
          ]}
          title="Blog ideas"
        />

        <BlogIdeaCardList
          ideas={ideas}
          approveIdeaAction={approveIdeaAction}
          rejectIdeaAction={rejectIdeaAction}
          generateOutlineAction={generateOutlineAction}
          generateDraftAction={generateDraftAction}
        />
      </div>
  );
}
