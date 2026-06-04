import { headers } from "next/headers";
import { notFound, redirect } from "next/navigation";

import { AdminCmsShell } from "@/components/admin/admin-cms-shell";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { ProjectEditor } from "@/components/admin/project-editor";
import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";
import { publishAction, saveDraftAction } from "@/app/admin/projects/editor/actions";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type AdminProjectDetail = {
  id: string;
  slug: string;
  title: string;
  description: string;
  content_markdown: string;
  image_url: string | null;
  status: string;
};

async function fetchProject(projectId: string): Promise<AdminProjectDetail> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await fetch(`${backendBaseUrl}/admin/projects/${projectId}`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch project: ${response.status}`);
  }

  return (await response.json()) as AdminProjectDetail;
}

type Props = {
  params: Promise<{ id: string }>;
};

export default async function AdminProjectEditPage({ params }: Props) {
  const { id } = await params;

  let project: AdminProjectDetail;
  try {
    project = await fetchProject(id);
  } catch {
    notFound();
  }

  return (
    <AdminCmsShell active="project-editor">
      <div className={adminPageStackClass}>
        <AdminPageHeader
          description={`Editing "${project.title}"`}
          eyebrow="Content workspace"
          title="Project editor"
        />

        <ProjectEditor
          initialContentMarkdown={project.content_markdown}
          initialDescription={project.description}
          initialImageUrl={project.image_url ?? ""}
          initialProjectId={project.id}
          initialSlug={project.slug}
          initialTitle={project.title}
          publishAction={publishAction}
          saveDraftAction={saveDraftAction}
        />
      </div>
    </AdminCmsShell>
  );
}
