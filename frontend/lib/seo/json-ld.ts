/**
 * JSON-LD structured data helpers for Schema.org.
 * Each function returns a JSON-LD object ready for `<script type="application/ld+json">`.
 */

const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "https://ailabportal.com";

/** WebSite schema — site-wide, add to root layout */
export function webSiteSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "AI Lab Portal",
    url: baseUrl,
    description:
      "Editorial AI engineering — exploring agent workflows, MCP integrations, and production AI patterns.",
    potentialAction: {
      "@type": "SearchAction",
      target: {
        "@type": "EntryPoint",
        urlTemplate: `${baseUrl}/blog?q={search_term_string}`,
      },
      "query-input": "required name=search_term_string",
    },
  };
}

/** Organization schema */
export function organizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "AI Lab Portal",
    url: baseUrl,
  };
}

/**
 * BlogPosting schema for individual blog articles.
 */
export function blogPostingSchema({
  headline,
  description,
  url,
  datePublished,
  dateModified,
  imageUrl,
  authorName,
  authorUrl,
}: {
  headline: string;
  description: string;
  url: string;
  datePublished: string;
  dateModified?: string;
  imageUrl?: string;
  authorName?: string;
  authorUrl?: string;
}) {
  const fullUrl = url.startsWith("http") ? url : `${baseUrl}${url}`;
  return {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline,
    description,
    url: fullUrl,
    datePublished,
    dateModified: dateModified ?? datePublished,
    ...(imageUrl && { image: imageUrl.startsWith("http") ? imageUrl : `${baseUrl}${imageUrl}` }),
    author: authorName
      ? {
          "@type": "Person",
          name: authorName,
          ...(authorUrl && { url: authorUrl.startsWith("http") ? authorUrl : `${baseUrl}${authorUrl}` }),
        }
      : undefined,
    publisher: {
      "@type": "Organization",
      name: "AI Lab Portal",
      url: baseUrl,
    },
    mainEntityOfPage: {
      "@type": "WebPage",
      "@id": fullUrl,
    },
  };
}

/**
 * BreadcrumbList schema for navigation paths.
 */
export function breadcrumbListSchema(items: { name: string; url: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: item.name,
      item: item.url.startsWith("http") ? item.url : `${baseUrl}${item.url}`,
    })),
  };
}

/**
 * ItemList schema for paginated content lists (blog index, tag pages).
 */
export function itemListSchema<T>({
  items,
  itemUrl,
  itemName,
  numberOfItems,
}: {
  items: T[];
  itemUrl: (item: T) => string;
  itemName: (item: T) => string;
  numberOfItems: number;
}) {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    numberOfItems,
    itemListElement: items.map((item, i) => ({
      "@type": "ListItem",
      position: i + 1,
      url: `${baseUrl}${itemUrl(item)}`,
      name: itemName(item),
    })),
  };
}
