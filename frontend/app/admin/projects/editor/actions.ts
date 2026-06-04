"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

export type ProjectEditorActionState = {
  message: string;
  projectId: string;
  status: "idle" | "draft" | "published" | "error";
};

type AdminSession = NonNullable<Awaited<ReturnType<typeof auth.api.getSession>>>;

function readRequiredField(formData: FormData, name: string): string {
  const value = formData.get(name);
  if (typeof value !== "string" || value.trim().length === 0) throw new Error(`Missing ${name}`);
  return value.trim();
}

async function callAdminApi(path: string, init: RequestInit, session: AdminSession) {
  const adminHeaders = createAdminBoundaryHeaders({ user: { id: session.user.id, email: session.user.email } });
  const response = await fetch(`${backendBaseUrl}${path}`, {
    ...init,
    headers: { "content-type": "application/json", ...adminHeaders, ...init.headers },
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`Admin API request failed: ${response.status}`);
  return response.json() as Promise<{ id: string; status: "draft" | "published" }>;
}

async function saveDraft(formData: FormData, session: AdminSession) {
  const projectId = formData.get("projectId");
  const imageUrlValue = formData.get("imageUrl");
  const payload: Record<string, string | null> = {
    title: readRequiredField(formData, "title"),
    slug: readRequiredField(formData, "slug"),
    description: readRequiredField(formData, "description"),
    content_markdown: readRequiredField(formData, "contentMarkdown"),
  };
  if (typeof imageUrlValue === "string" && imageUrlValue.trim().length > 0) {
    payload.image_url = imageUrlValue.trim();
  }
  if (typeof projectId === "string" && projectId.trim().length > 0) {
    return callAdminApi(`/admin/projects/${projectId.trim()}`, { method: "PATCH", body: JSON.stringify(payload) }, session);
  }
  return callAdminApi("/admin/projects", { method: "POST", body: JSON.stringify(payload) }, session);
}

export async function saveDraftAction(
  previous: ProjectEditorActionState,
  formData: FormData
): Promise<ProjectEditorActionState> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  void previous;
  try {
    const item = await saveDraft(formData, session);
    return { message: "Draft saved", projectId: item.id, status: "draft" };
  } catch (error) {
    return { message: error instanceof Error ? error.message : "Save failed", projectId: "", status: "error" };
  }
}

export async function publishAction(
  previous: ProjectEditorActionState,
  formData: FormData
): Promise<ProjectEditorActionState> {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  try {
    const saved = previous.projectId ? { id: previous.projectId, status: previous.status } : await saveDraft(formData, session);
    const published = await callAdminApi(`/admin/projects/${saved.id}/publish`, { method: "POST" }, session);
    return { message: "Project published", projectId: published.id, status: "published" };
  } catch (error) {
    return {
      message: error instanceof Error ? error.message : "Publish failed",
      projectId: previous.projectId,
      status: "error",
    };
  }
}
