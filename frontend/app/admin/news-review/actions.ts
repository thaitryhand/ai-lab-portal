"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

async function adminFetch(url: string, init?: RequestInit, session?: Awaited<ReturnType<typeof auth.api.getSession>>) {
  if (!session) redirect("/admin/login");

  return fetch(`${backendBaseUrl}${url}`, {
    ...init,
    headers: {
      ...createAdminBoundaryHeaders({
        user: { id: session.user.id, email: session.user.email },
      }),
      ...(init?.headers ?? {}),
    },
  });
}

async function mutateReviewItem(reviewId: string, action: "approve" | "reject" | "publish" | "unpublish") {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/admin/login");

  const response = await adminFetch(
    `/admin/news/review-items/${reviewId}/${action}`,
    { method: "POST" },
    session,
  );

  if (!response.ok) {
    throw new Error(`Failed to ${action} AI news review item: ${response.status}`);
  }

  redirect("/admin/news-review");
}

function readReviewId(formData: FormData) {
  const reviewId = formData.get("reviewId");
  if (typeof reviewId !== "string" || reviewId.length === 0) {
    throw new Error("Missing review item id");
  }
  return reviewId;
}

export async function approveReviewItemAction(formData: FormData) {
  await mutateReviewItem(readReviewId(formData), "approve");
}

export async function rejectReviewItemAction(formData: FormData) {
  await mutateReviewItem(readReviewId(formData), "reject");
}

export async function publishReviewItemAction(formData: FormData) {
  await mutateReviewItem(readReviewId(formData), "publish");
}

export async function unpublishReviewItemAction(formData: FormData) {
  await mutateReviewItem(readReviewId(formData), "unpublish");
}
