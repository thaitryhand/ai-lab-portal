import { headers as nextHeaders } from "next/headers";

import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

/**
 * Proxy POST /admin/blog-ideas/generate-stream/* from the backend.
 *
 * Supports multiple streaming endpoints via catch-all route:
 * - /api/.../generate-stream/idea (payload = project context fields)
 * - /api/.../generate-stream/outline (payload = { ideaId })
 * - /api/.../generate-stream/draft (payload = { ideaId })
 * - /api/.../generate-stream/review (payload = { ideaId })
 * - /api/.../generate-stream/marketing (payload = { ideaId })
 *
 * The client sends a JSON body with the generation fields.
 * For per-stage endpoints, the body includes an ``ideaId``.
 */
export async function POST(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const session = await auth.api.getSession({
    headers: await nextHeaders(),
  });
  if (!session?.user?.id) {
    return new Response("Unauthorized", { status: 401 });
  }

  const payload = await request.json();
  const authHeaders = createAdminBoundaryHeaders({
    user: { id: session.user.id, email: session.user.email },
  });

  // Determine the backend streaming endpoint from catch-all path
  const { path } = await params;
  const streamType = path?.[0]; // first segment after "generate-stream"

  let backendPath: string;
  if (streamType && streamType !== "generate-stream") {
    // Per-stage endpoint: /{idea_id}/generate-stream/{stage}
    const ideaId = payload.ideaId;
    if (!ideaId) {
      return new Response(
        JSON.stringify({ error: "ideaId is required for stage streaming" }),
        { status: 400, headers: { "Content-Type": "application/json" } },
      );
    }
    backendPath = `/admin/blog-ideas/${ideaId}/generate-stream/${streamType}`;
  } else {
    // Idea generation endpoint: payload has project context fields
    backendPath = `/admin/blog-ideas/generate-stream/idea`;
  }

  const backendResponse = await fetch(
    `${backendBaseUrl}${backendPath}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
      },
      body: JSON.stringify(payload),
    },
  );

  if (!backendResponse.ok) {
    return new Response(
      JSON.stringify({
        error: `Backend returned ${backendResponse.status}`,
        detail: await backendResponse.text().catch(() => ""),
      }),
      {
        status: backendResponse.status,
        headers: { "Content-Type": "application/json" },
      },
    );
  }

  // Return the SSE stream directly
  return new Response(backendResponse.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
