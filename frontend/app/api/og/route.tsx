import { ImageResponse } from "@vercel/og";

export const runtime = "edge";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);

    const title = searchParams.get("title") ?? "AI Lab Portal";
    const author = searchParams.get("author");
    const excerpt = searchParams.get("excerpt");

    return new ImageResponse(
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          width: "100%",
          height: "100%",
          padding: "64px 80px",
          background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
          color: "#f8fafc",
          fontFamily: "'Inter', 'SF Pro', system-ui, sans-serif",
        }}
      >
        {/* Top branding */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            marginBottom: 40,
          }}
        >
          <div
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: "#6366f1",
            }}
          />
          <span
            style={{
              fontSize: 16,
              fontWeight: 500,
              color: "#94a3b8",
              letterSpacing: "0.15em",
              textTransform: "uppercase" as const,
            }}
          >
            AI Lab Portal
          </span>
        </div>

        {/* Title */}
        <div
          style={{
            display: "flex",
            flex: 1,
            flexDirection: "column",
            justifyContent: "center",
            gap: 16,
          }}
        >
          <h1
            style={{
              fontSize: 56,
              fontWeight: 700,
              lineHeight: 1.2,
              letterSpacing: "-0.02em",
              margin: 0,
              color: "#f8fafc",
              overflow: "hidden",
              textOverflow: "ellipsis",
              display: "-webkit-box",
              WebkitLineClamp: 3,
              WebkitBoxOrient: "vertical",
            }}
          >
            {title}
          </h1>

          {excerpt && (
            <p
              style={{
                fontSize: 24,
                fontWeight: 400,
                color: "#94a3b8",
                lineHeight: 1.4,
                margin: 0,
                maxWidth: 600,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {excerpt}
            </p>
          )}
        </div>

        {/* Bottom bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 24,
            paddingTop: 24,
            borderTop: "1px solid #334155",
          }}
        >
          <span style={{ fontSize: 18, color: "#64748b" }}>
            {author ?? "AI Lab Team"}
          </span>
          <span style={{ fontSize: 14, color: "#475569" }}>ailabportal.com</span>
        </div>
      </div>,
      {
        width: 1200,
        height: 630,
      }
    );
  } catch {
    return new Response("Failed to generate OG image", { status: 500 });
  }
}
