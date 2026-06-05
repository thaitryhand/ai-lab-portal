/**
 * Estimate reading time from markdown content.
 * Strips markdown syntax, counts words, divides by average reading speed.
 *
 * Average reading speed: 200 WPM for English technical content.
 */
const WPM = 200;

/** Strip common markdown syntax to get plain text word count. */
function stripMarkdown(md: string): string {
  return md
    // Code blocks → remove entirely (counted separately)
    .replace(/```[\s\S]*?```/g, "")
    .replace(/`[^`]+`/g, "")
    // Headers
    .replace(/^#{1,6}\s+/gm, "")
    // Bold / italic
    .replace(/[*_]{1,3}([^*_]+)[*_]{1,3}/g, "$1")
    // Links
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    // Images
    .replace(/!\[([^\]]*)\]\([^)]+\)/g, "")
    // Blockquotes
    .replace(/^>\s+/gm, "")
    // Horizontal rules
    .replace(/^---+/gm, "")
    // HTML tags
    .replace(/<[^>]+>/g, "")
    // List markers
    .replace(/^[-*+]\s+/gm, "")
    .replace(/^\d+\.\s+/gm, "")
    // Clean up whitespace
    .replace(/\s+/g, " ")
    .trim();
}

export function estimateReadingTime(markdown: string): number {
  if (!markdown) return 0;
  const text = stripMarkdown(markdown);
  const words = text.split(/\s+/).filter(Boolean).length;
  const minutes = Math.ceil(words / WPM);
  return Math.max(1, minutes);
}

export function formatReadingTime(minutes: number): string {
  return `${minutes} min read`;
}
