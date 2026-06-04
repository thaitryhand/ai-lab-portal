import { NextResponse } from "next/server";
import { headers } from "next/headers";

import { auth } from "@/lib/auth/server";
import { toggleBookmark } from "@/lib/blog/social";

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ slug: string }> }
) {
  const { slug } = await params;
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) {
    return NextResponse.json({ error: "Not authenticated" }, { status: 401 });
  }

  try {
    const result = await toggleBookmark(slug, session);
    return NextResponse.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to toggle bookmark";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
