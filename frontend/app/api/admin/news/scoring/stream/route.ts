import { headers as nextHeaders } from "next/headers";

import { createAdminBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

export const dynamic = "force-dynamic";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

/**
 * Proxy POST /admin/news/scoring/stream from the backend.
 *
 * The client sends a JSON body with { articleId } (or empty).
 * This route gets the admin session, creates HMAC-signed auth headers,
 * forwards the article_id as a query param, and streams SSE back.
 */
export async function POST(request: Request) {
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

  const url = new URL(request.url);
  const articleId = url.searchParams.get("article_id") || payload.articleId;

  if (!articleId) {
    return new Response(
      JSON.stringify({ error: "article_id is required" }),
      { status: 400, headers: { "Content-Type": "application/json" } },
    );
  }

  const backendResponse = await fetch(
    `${backendBaseUrl}/admin/news/scoring/stream?article_id=${encodeURIComponent(articleId)}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
      },
      body: JSON.stringify({}),
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

  return new Response(backendResponse.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
