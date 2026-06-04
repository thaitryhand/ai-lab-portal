import { NextResponse } from "next/server";
import { headers } from "next/headers";

import { auth } from "@/lib/auth/server";
import { checkBookmark } from "@/lib/blog/social";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ slug: string }> }
) {
  const { slug } = await params;
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) {
    return NextResponse.json(false);
  }

  try {
    const result = await checkBookmark(slug, session);
    return NextResponse.json(result);
  } catch {
    return NextResponse.json(false);
  }
}
