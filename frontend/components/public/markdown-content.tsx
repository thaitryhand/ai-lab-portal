import type { ComponentProps } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

import { publicProseClass } from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

type MarkdownContentProps = {
  className?: string;
  markdown: string;
};

/**
 * Tailwind prose classes that mirror the Tiptap editor typography
 * for a consistent authoring-to-display experience.
 *
 * Key differences from default `prose`:
 * - Heading sizes match the editor (smaller than prose defaults)
 * - Code blocks get highlight.js syntax highlighting
 * - Blockquote styling matches editor (left accent bar)
 * - Task lists render as styled checkboxes
 */
const proseOverrides =
  "prose prose-neutral max-w-none dark:prose-invert " +
  /* Headings — match editor sizing */
  "prose-h1:text-[1.375rem] prose-h1:leading-7 prose-h1:tracking-[-0.004375rem] prose-h1:mt-[46px] prose-h1:mb-4 " +
  "prose-h2:text-[1.1875rem] prose-h2:leading-7 prose-h2:tracking-[0.003125rem] prose-h2:mt-8 prose-h2:mb-3.5 " +
  "prose-h3:text-[1.0625rem] prose-h3:leading-6 prose-h3:tracking-[0.00625rem] prose-h3:mt-6 prose-h3:mb-3 " +
  "prose-h4:text-[0.9375rem] prose-h4:leading-6 prose-h4:mt-4 prose-h4:mb-2 " +
  "prose-headings:font-[family-name:var(--font-gt-super)] prose-headings:font-normal prose-headings:tracking-[-0.03em] " +
  /* Paragraphs */
  "prose-p:text-lg prose-p:leading-8 " +
  /* Blockquotes — match editor: plain left bar, no rounded corners */
  "prose-blockquote:border-l-[3px] prose-blockquote:border-accent-foreground/15 prose-blockquote:bg-transparent prose-blockquote:not-italic prose-blockquote:font-normal prose-blockquote:py-0 prose-blockquote:pl-3.5 prose-blockquote:pr-0 " +
  /* Images */
  "prose-img:rounded-xl prose-img:border prose-img:border-border/50 prose-img:shadow-sm prose-img:mx-auto " +
  /* Links */
  "prose-a:font-semibold prose-a:text-brand prose-a:underline prose-a:underline-offset-4 hover:prose-a:underline " +
  /* Inline code */
  "prose-code:rounded prose-code:border prose-code:border-[var(--mt-code-color,#d4d4d4)] prose-code:bg-[var(--mt-code-background,#ffffff13)] prose-code:px-1 prose-code:py-0.5 prose-code:text-sm prose-code:font-normal prose-code:before:content-none prose-code:after:content-none " +
  /* Code blocks */
  "prose-pre:rounded-lg prose-pre:border prose-pre:border-border/70 prose-pre:bg-[var(--mt-pre-background,#080808)] prose-pre:text-[var(--mt-pre-color,#e3e4e6)] prose-pre:shadow-sm " +
  /* Lists */
  "prose-li:my-0 ";

/**
 * Highlight.js CSS theme matching the editor's dark code colors.
 * We import the highlight.js theme CSS in globals.css or here.
 */
const highlightStyles = {
  "& :where(pre) code": {
    backgroundColor: "transparent",
    border: "none",
    padding: 0,
  },
  // Ensure highlight.js tokens are visible in dark mode
  "& .hljs": {
    color: "var(--mt-pre-color, #e3e4e6)",
    background: "transparent",
  },
};

export function MarkdownContent({ className, markdown }: MarkdownContentProps) {
  if (!markdown.trim()) {
    return null;
  }

  return (
    <div
      className={cn(
        publicProseClass,
        proseOverrides,
        className,
      )}
      style={highlightStyles as React.CSSProperties}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[
          [rehypeHighlight, { detect: true, ignoreMissing: true }],
        ]}
        components={{
          img: (props: ComponentProps<"img"> & { node?: unknown }) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              loading="lazy"
              decoding="async"
              alt={props.alt ?? ""}
              {...props}
            />
          ),
          // Render task list items as styled checkboxes (like the editor)
          input: (props: ComponentProps<"input"> & { node?: unknown }) => {
            if (props.type === "checkbox") {
              return (
                <input
                  type="checkbox"
                  checked={props.checked ?? false}
                  readOnly
                  className="mt-1.5 size-4 cursor-default rounded border-border accent-primary"
                  {...props}
                />
              );
            }
            return <input {...props} />;
          },
          // Style code blocks consistently
          code: ({
            className: codeClassName,
            children,
            ...props
          }: ComponentProps<"code"> & { node?: unknown }) => {
            const isBlock = codeClassName?.startsWith("language-");
            if (isBlock) {
              return (
                <code className={codeClassName} {...props}>
                  {children}
                </code>
              );
            }
            return (
              <code className={codeClassName} {...props}>
                {children}
              </code>
            );
          },
          // Style pre blocks
          pre: (props: ComponentProps<"pre"> & { node?: unknown }) => {
            return <pre {...props} />;
          },
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
