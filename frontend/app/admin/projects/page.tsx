import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { AdminCmsShell } from "@/components/admin/admin-cms-shell";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { AdminListToolbar } from "@/components/admin/admin-list-toolbar";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { ProjectCardList } from "./project-card-list";
import { publishFromListAction, unpublishFromListAction } from "./actions";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

export type AdminProject = {
  id: string;
  slug: string;
  title: string;
  status: "draft" | "published";
  published_at: string | null;
  image_url: string | null;
};

async function listAdminProjects() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}/admin/projects`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch admin projects: ${response.status}`);
  }

  return (await response.json()) as AdminProject[];
}

export default async function AdminProjectsListPage() {
  const items = await listAdminProjects();
  const publishedCount = items.filter((item) => item.status === "published").length;
  const draftCount = items.length - publishedCount;

  return (
    <AdminCmsShell active="projects">
      <div className={adminPageStackClass}>
        <AdminListToolbar
          ctaHref="/admin/projects/editor"
          ctaLabel="New project"
          description="Manage company projects and internal tools with publish workflow."
          eyebrow="Projects"
          metrics={[
            { dotClassName: "bg-brand", label: `${publishedCount} live` },
            { dotClassName: "bg-amber-500", label: `${draftCount} drafts` },
            { dotClassName: "bg-muted-foreground", label: `${items.length} total` },
          ]}
          title="Projects"
        />

        <ProjectCardList
          items={items}
          publishAction={publishFromListAction}
          unpublishAction={unpublishFromListAction}
        />
      </div>
    </AdminCmsShell>
  );
}
