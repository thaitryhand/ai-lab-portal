import { listPublishedBlogPosts } from "@/lib/blog/posts";

const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://ailabportal.com";
const siteName = "AI Lab Portal";

function escapeXml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export async function GET() {
  const posts = await listPublishedBlogPosts();

  const items = posts
    .map(
      (post) => `
    <item>
      <title>${escapeXml(post.title)}</title>
      <link>${siteUrl}/blog/${post.slug}</link>
      <guid isPermaLink="true">${siteUrl}/blog/${post.slug}</guid>
      <description>${escapeXml(post.excerpt)}</description>
      <pubDate>${new Date(post.publishedAt).toUTCString()}</pubDate>
      <author>${escapeXml(post.authorName)}</author>
      ${post.imageUrl ? `<enclosure url="${escapeXml(post.imageUrl)}" type="image/jpeg" />` : ""}
    </item>`
    )
    .join("\n");

  const rss = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>${escapeXml(siteName)} Blog</title>
    <link>${siteUrl}/blog</link>
    <description>Practical AI engineering notes and human-reviewed AI Lab articles.</description>
    <language>en</language>
    <lastBuildDate>${posts.length > 0 ? new Date(posts[0].publishedAt).toUTCString() : new Date().toUTCString()}</lastBuildDate>
    <atom:link href="${siteUrl}/blog/feed" rel="self" type="application/rss+xml" />
    ${items}
  </channel>
</rss>`;

  return new Response(rss, {
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8",
      "Cache-Control": "max-age=0, s-maxage=3600, stale-while-revalidate",
    },
  });
}
