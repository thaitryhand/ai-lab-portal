import { NextRequest, NextResponse } from "next/server";
import { headers as nextHeaders } from "next/headers";

import { createUserBoundaryHeaders } from "@/lib/admin/fastapi-boundary";
import { auth } from "@/lib/auth/server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

async function getAuthSession() {
  return auth.api.getSession({ headers: await nextHeaders() });
}

function getBackendHeaders(session: NonNullable<Awaited<ReturnType<typeof auth.api.getSession>>>) {
  return createUserBoundaryHeaders({
    user: { id: session.user.id, email: session.user.email },
  });
}

export async function GET(request: NextRequest) {
  const session = await getAuthSession();
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { searchParams } = request.nextUrl;
  const path = searchParams.get("path") ?? "";

  let backendPath = "/public/notifications";
  if (path) {
    backendPath += `/${path}`;
  }

  const userHeaders = getBackendHeaders(session);

  try {
    const response = await fetch(`${backendBaseUrl}${backendPath}`, {
      headers: { "content-type": "application/json", ...userHeaders },
      cache: "no-store",
    });

    if (!response.ok) {
      return NextResponse.json({ error: "Backend request failed" }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "Failed to fetch notifications" }, { status: 502 });
  }
}

export async function POST(request: NextRequest) {
  const session = await getAuthSession();
  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { path, method } = await request.json().catch(() => ({ path: "", method: "" }));
  const userHeaders = getBackendHeaders(session);

  let backendPath = "/public/notifications";
  if (path) {
    backendPath += `/${path}`;
  }

  try {
    const response = await fetch(`${backendBaseUrl}${backendPath}`, {
      method: method ?? "POST",
      headers: { "content-type": "application/json", ...userHeaders },
      cache: "no-store",
    });

    if (!response.ok) {
      return NextResponse.json({ error: "Backend request failed" }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: "Failed to send request" }, { status: 502 });
  }
}
