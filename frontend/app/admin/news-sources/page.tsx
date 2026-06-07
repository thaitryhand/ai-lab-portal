import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { AdminListToolbar } from "@/components/admin/admin-list-toolbar";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { NewsSourceCardList } from "./news-source-card-list";
import { toggleNewsSourceAction } from "./actions";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

export type AdminNewsSource = {
  id: string;
  name: string;
  source_type: "rss" | "github" | "website" | "hackernews";
  url_or_identifier: string;
  priority: "high" | "medium" | "low";
  is_enabled: boolean;
  last_crawled_at: string | null;
};

async function listNewsSources() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const response = await fetch(`${backendBaseUrl}/admin/news-sources`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Failed to fetch news sources: ${response.status}`);
  return (await response.json()) as AdminNewsSource[];
}

export default async function AdminNewsSourcesPage() {
  const items = await listNewsSources();
  const enabledCount = items.filter((item) => item.is_enabled).length;

  return (
      <div className={adminPageStackClass}>
        <AdminListToolbar
          ctaHref="/admin/news-sources/new"
          ctaLabel="Add source"
          description="Configure official RSS, GitHub, and website feeds for the AI News pipeline."
          eyebrow="AI News"
          metrics={[
            { dotClassName: "bg-brand", label: `${enabledCount} enabled` },
            { dotClassName: "bg-muted-foreground", label: `${items.length} total` },
          ]}
          title="News sources"
        />
        <NewsSourceCardList items={items} toggleAction={toggleNewsSourceAction} />
      </div>
  );
}
