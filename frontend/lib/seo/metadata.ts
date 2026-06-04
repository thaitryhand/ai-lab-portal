import type { Metadata } from "next";

const siteName = "AI Lab Portal";

const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://ailabportal.com";

export function createPublicMetadata({
  title,
  description,
  ogImageUrl,
  path,
  type = "website",
}: {
  title: string;
  description: string;
  ogImageUrl?: string;
  path: string;
  type?: "website" | "article";
}): Metadata {
  const canonicalPath = path.startsWith("/") ? path : `/${path}`;
  const image = ogImageUrl ?? `${baseUrl}/api/og?title=${encodeURIComponent(title)}&description=${encodeURIComponent(description)}`;

  return {
    title,
    description,
    alternates: {
      canonical: canonicalPath,
    },
    openGraph: {
      title,
      description,
      siteName,
      type,
      url: canonicalPath,
      images: [{ url: image, width: 1200, height: 630 }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [image],
    },
  };
}
