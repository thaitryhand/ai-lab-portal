import { NextResponse } from "next/server";

const backendBaseUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:18000";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const response = await fetch(`${backendBaseUrl}/health`, {
      signal: AbortSignal.timeout(8_000),
    });

    if (!response.ok) {
      return NextResponse.json(
        { status: "error", backend_http: response.status },
        { status: 502 },
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      {
        status: "unreachable",
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 503 },
    );
  }
}
