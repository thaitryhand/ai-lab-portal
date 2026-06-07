import { headers as nextHeaders } from "next/headers";

import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

/**
 * Proxy PATCH /admin/blog-ideas/{ideaId}/schedule.
 */
export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ ideaId: string }> },
) {
  const session = await auth.api.getSession({
    headers: await nextHeaders(),
  });
  if (!session?.user?.id) {
    return new Response("Unauthorized", { status: 401 });
  }

  const { ideaId } = await params;
  const body = await request.json();

  const response = await fetch(
    `${backendBaseUrl}/admin/blog-ideas/${ideaId}/schedule`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...createAdminBoundaryHeaders({
          user: { id: session.user.id, email: session.user.email },
        }),
      },
      body: JSON.stringify(body),
    },
  );

  if (!response.ok) {
    return new Response(response.body, { status: response.status });
  }

  const data = await response.json();
  return Response.json(data);
}
