"use server";

import { revalidatePath } from "next/cache";
import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

type AdminSession = NonNullable<Awaited<ReturnType<typeof auth.api.getSession>>>;

async function callMutation(path: string, session: AdminSession) {
  const response = await fetch(`${backendBaseUrl}${path}`, {
    method: "POST",
    headers: createAdminBoundaryHeaders({ user: { id: session.user.id, email: session.user.email } }),
    cache: "no-store",
  });

  if (!response.ok) throw new Error(`Admin API mutation failed: ${response.status}`);
  revalidatePath("/admin/projects");
  revalidatePath("/projects");
}

export async function publishFromListAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const projectId = formData.get("projectId");
  if (typeof projectId !== "string" || projectId.length === 0) throw new Error("Missing projectId");
  await callMutation(`/admin/projects/${projectId}/publish`, session);
}

export async function unpublishFromListAction(formData: FormData) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");
  const projectId = formData.get("projectId");
  if (typeof projectId !== "string" || projectId.length === 0) throw new Error("Missing projectId");
  await callMutation(`/admin/projects/${projectId}/unpublish`, session);
}
