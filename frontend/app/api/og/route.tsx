import { ImageResponse } from "@vercel/og";
import path from "path";
import fs from "fs";

export const runtime = "nodejs";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);

    const title = searchParams.get("title") ?? "AI Lab Portal";
    const description = searchParams.get("description") ?? "Editorial AI engineering";
    const authorName = searchParams.get("author") ?? null;
    const readingTime = searchParams.get("readingTime") ?? null;

    const displayTitle =
      title.length > 90 ? title.slice(0, 87) + "…" : title;
    const displayDesc =
      description.length > 160
        ? description.slice(0, 157) + "…"
        : description;

    // Load Geist font from node_modules
    const fontPath = path.resolve(
      process.cwd(),
      "node_modules/@vercel/og/dist/Geist-Regular.ttf"
    );
    const fontData = fs.readFileSync(fontPath);

    return new ImageResponse(
      (
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            flexDirection: "column",
            background:
              "linear-gradient(145deg, #0b0d0e 0%, #111315 40%, #141618 100%)",
            fontFamily: "Geist",
          }}
        >
          {/* Subtle grid pattern */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundImage:
                "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.03) 1px, transparent 0)",
              backgroundSize: "32px 32px",
            }}
          />

          {/* Accent line */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              height: "3px",
              background:
                "linear-gradient(90deg, #4f8c7a 0%, #6abf9e 50%, #4f8c7a 100%)",
            }}
          />

          {/* Top section */}
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "space-between",
              padding: "48px 56px 0",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
              }}
            >
              <div
                style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "10px",
                  background:
                    "linear-gradient(135deg, #4f8c7a 0%, #6abf9e 100%)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#fff",
                  fontSize: "18px",
                  fontWeight: 700,
                }}
              >
                AI
              </div>
              <span
                style={{
                  fontSize: "20px",
                  fontWeight: 500,
                  color: "#e6e8ea",
                  letterSpacing: "-0.02em",
                }}
              >
                AI Lab Portal
              </span>
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "16px",
              }}
            >
              {readingTime && (
                <span
                  style={{
                    fontSize: "14px",
                    color: "#7a8288",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "20px",
                    padding: "6px 14px",
                  }}
                >
                  {readingTime} min read
                </span>
              )}
              {authorName && (
                <span
                  style={{
                    fontSize: "14px",
                    color: "#9ca3af",
                  }}
                >
                  By {authorName}
                </span>
              )}
            </div>
          </div>

          {/* Main content */}
          <div
            style={{
              flex: 1,
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              padding: "0 56px",
            }}
          >
            <h1
              style={{
                fontSize: displayTitle.length > 60 ? "36px" : "44px",
                fontWeight: 600,
                color: "#f0f2f4",
                lineHeight: 1.2,
                letterSpacing: "-0.03em",
                margin: "0 0 16px 0",
                maxWidth: "800px",
              }}
            >
              {displayTitle}
            </h1>
            {displayDesc && (
              <p
                style={{
                  fontSize: "18px",
                  color: "#8e959c",
                  lineHeight: 1.5,
                  margin: 0,
                  maxWidth: "680px",
                }}
              >
                {displayDesc}
              </p>
            )}
          </div>

          {/* Bottom bar */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "32px 56px 40px",
              borderTop: "1px solid rgba(255,255,255,0.06)",
            }}
          >
            <span
              style={{
                fontSize: "13px",
                color: "#5a6268",
                letterSpacing: "0.04em",
                textTransform: "uppercase",
              }}
            >
              ailabportal.com
            </span>
            <span
              style={{
                fontSize: "13px",
                color: "#5a6268",
              }}
            >
              Editorial AI Engineering
            </span>
          </div>
        </div>
      ),
      {
        width: 1200,
        height: 630,
        fonts: [
          {
            name: "Geist",
            data: fontData,
            style: "normal",
            weight: 400,
          },
        ],
      }
    );
  } catch (e) {
    console.error("OG image generation failed:", e);
    return new Response(
      `OG image generation failed: ${e instanceof Error ? e.message : String(e)}`,
      { status: 500 }
    );
  }
}
