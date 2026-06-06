import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

export type ContextPickerItem = {
  id: string;
  title: string;
  status: "draft" | "published";
};

export type ProjectContextDetail = {
  id: string;
  title: string;
  description: string;
  content_markdown: string;
};

export type ShowcaseContextDetail = {
  id: string;
  title: string;
  hero_summary: string;
  industry: string | null;
  use_case: string | null;
  content_markdown: string;
};

async function adminSession() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  return session;
}

async function adminFetch(path: string) {
  const session = await adminSession();
  return fetch(`${backendBaseUrl}${path}`, {
    headers: createAdminBoundaryHeaders({
      user: { id: session.user.id, email: session.user.email },
    }),
    cache: "no-store",
  });
}

export async function listContextPickerProjects(): Promise<ContextPickerItem[]> {
  const response = await adminFetch("/admin/projects");
  if (!response.ok) return [];
  const items = (await response.json()) as ContextPickerItem[];
  return items.sort((a, b) => a.title.localeCompare(b.title));
}

export async function listContextPickerShowcases(): Promise<ContextPickerItem[]> {
  const response = await adminFetch("/admin/showcases");
  if (!response.ok) return [];
  const items = (await response.json()) as ContextPickerItem[];
  return items.sort((a, b) => a.title.localeCompare(b.title));
}

export async function fetchProjectContextDetail(
  projectId: string,
): Promise<ProjectContextDetail | undefined> {
  const response = await adminFetch(`/admin/projects/${projectId}`);
  if (response.status === 404) return undefined;
  if (!response.ok) {
    throw new Error(`Failed to fetch project: ${response.status}`);
  }
  return (await response.json()) as ProjectContextDetail;
}

export async function fetchShowcaseContextDetail(
  showcaseId: string,
): Promise<ShowcaseContextDetail | undefined> {
  const response = await adminFetch(`/admin/showcases/${showcaseId}`);
  if (response.status === 404) return undefined;
  if (!response.ok) {
    throw new Error(`Failed to fetch showcase: ${response.status}`);
  }
  return (await response.json()) as ShowcaseContextDetail;
}
