import type { Metadata } from "next";

const siteName = "AI Lab Portal";

const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://ailabportal.com";

export function createPublicMetadata({
  title,
  description,
  ogImageUrl,
  ogAuthor,
  ogReadingTime,
  path,
  type = "website",
}: {
  title: string;
  description: string;
  ogImageUrl?: string;
  ogAuthor?: string;
  ogReadingTime?: number;
  path: string;
  type?: "website" | "article";
}): Metadata {
  const canonicalPath = path.startsWith("/") ? path : `/${path}`;
  const ogParams = new URLSearchParams({ title, description });
  if (ogAuthor) ogParams.set("author", ogAuthor);
  if (ogReadingTime) ogParams.set("readingTime", String(ogReadingTime));
  const image = ogImageUrl ?? `${baseUrl}/api/og?${ogParams.toString()}`;

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
