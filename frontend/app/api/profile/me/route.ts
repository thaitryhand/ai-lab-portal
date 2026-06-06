import { headers } from "next/headers";
import { NextResponse } from "next/server";

import { auth } from "@/lib/auth/server";
import { getMyProfile } from "@/lib/user/profile";

export async function GET() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) {
    return NextResponse.json({ profile: null }, { status: 401 });
  }

  const profile = await getMyProfile(session);
  return NextResponse.json({ profile });
}
