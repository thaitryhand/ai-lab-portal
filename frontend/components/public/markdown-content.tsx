import type { ComponentProps } from "react";
import { useState } from "react";
import { Copy, Check, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";

import { publicProseClass } from "@/components/public/public-ui";
import { isRenderableImageSrc } from "@/lib/sanitize-blog-markdown";
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
  "prose-li:my-0 " +
  /* Tables — match editor layout */
  "prose-table:w-full prose-table:border-collapse prose-table:text-sm " +
  "prose-th:border prose-th:border-border/70 prose-th:bg-muted/50 prose-th:px-3 prose-th:py-2 prose-th:text-left prose-th:font-semibold prose-th:text-foreground " +
  "prose-td:border prose-td:border-border/70 prose-td:px-3 prose-td:py-2 prose-td:text-foreground/80 " +
  "prose-tr:even:bg-muted/20 ";

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

function ImageLightbox({ src, alt, onClose }: { src: string; alt: string; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Image preview"
    >
      <button
        type="button"
        className="absolute right-4 top-4 rounded-full bg-black/50 p-2 text-white transition-colors hover:bg-black/70"
        onClick={onClose}
        aria-label="Close preview"
      >
        <X className="h-5 w-5" />
      </button>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={src}
        alt={alt}
        className="max-h-[90vh] max-w-[90vw] rounded-lg object-contain shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      />
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  return (
    <button
      type="button"
      className="absolute right-2 top-2 rounded-md bg-white/10 p-1.5 text-white/60 opacity-0 transition-all hover:bg-white/20 hover:text-white/90 group-hover/pre:opacity-100"
      onClick={async () => {
        await navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      aria-label="Copy code"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-green-400" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────


export function MarkdownContent({ className, markdown }: MarkdownContentProps) {
  const [lightboxSrc, setLightboxSrc] = useState<string | null>(null);

  if (!markdown.trim()) {
    return null;
  }

  // Extract code content for copy buttons
  let codeBlockCounter = 0;

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
          img: ({
            src,
            alt,
            title,
            ...rest
          }: ComponentProps<"img"> & { node?: unknown }) => {
            const resolvedSrc = typeof src === "string" ? src : undefined;
            if (!isRenderableImageSrc(resolvedSrc)) {
              return null;
            }

            return (
              // eslint-disable-next-line @next/next/no-img-element
              <button
                type="button"
                className="cursor-zoom-in border-0 bg-transparent p-0"
                onClick={() => setLightboxSrc(resolvedSrc!)}
                aria-label="Zoom image"
              >
                <img
                  loading="lazy"
                  decoding="async"
                  alt={alt ?? ""}
                  title={title}
                  src={resolvedSrc}
                  className="rounded-xl border border-border/50 shadow-sm transition-transform hover:scale-[1.02]"
                  {...rest}
                />
              </button>
            );
          },
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
          // Style pre blocks — add copy button
          pre: ({ children, ...props }: ComponentProps<"pre"> & { node?: unknown }) => {
            codeBlockCounter++;
            // Extract text content from children for copy
            let codeText = "";
            try {
              const childArr = Array.isArray(children) ? children : [children];
              for (const child of childArr) {
                if (typeof child === "string") codeText += child;
                else if (child && typeof child === "object" && "props" in child) {
                  const grandChildren = (child as { props?: { children?: unknown } }).props?.children;
                  if (typeof grandChildren === "string") codeText += grandChildren;
                }
              }
            } catch {
              // ignore
            }

            return (
              <div className="group/pre relative">
                <pre {...props}>{children}</pre>
                <CopyButton text={codeText} />
              </div>
            );
          },
        }}
      >
        {markdown}
      </ReactMarkdown>

      {/* Image lightbox */}
      {lightboxSrc && (
        <ImageLightbox
          src={lightboxSrc}
          alt=""
          onClose={() => setLightboxSrc(null)}
        />
      )}
    </div>
  );
}
