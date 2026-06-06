/** Patterns for inline images that must not be persisted or rendered publicly. */
const EMPTY_IMAGE_MARKDOWN = /!\[[^\]]*\]\(\s*\)/g;
const BLOB_IMAGE_MARKDOWN = /!\[[^\]]*\]\(blob:[^)]+\)/g;

export function hasPendingBlogImages(markdown: string): boolean {
  return /!\[[^\]]*\]\(blob:[^)]+\)/.test(markdown) || /!\[[^\]]*\]\(\s*\)/.test(markdown);
}

/** Remove broken image markdown (empty URL or ephemeral blob URLs). */
export function stripBrokenBlogImages(markdown: string): string {
  return markdown
    .replace(EMPTY_IMAGE_MARKDOWN, "")
    .replace(BLOB_IMAGE_MARKDOWN, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

export function isRenderableImageSrc(src: string | undefined | null): src is string {
  if (typeof src !== "string") return false;
  const trimmed = src.trim();
  if (!trimmed) return false;
  if (trimmed.startsWith("blob:")) return false;
  return true;
}
