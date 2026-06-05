import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { publicProseClass } from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

type MarkdownContentProps = {
  className?: string;
  markdown: string;
};

export function MarkdownContent({ className, markdown }: MarkdownContentProps) {
  if (!markdown.trim()) {
    return null;
  }

  return (
    <div
      className={cn(
        publicProseClass,
        "prose prose-neutral max-w-none dark:prose-invert",
        "prose-headings:font-[family-name:var(--font-gt-super)] prose-headings:font-normal prose-headings:tracking-[-0.03em]",
        "prose-p:text-lg prose-p:leading-8 prose-blockquote:rounded-2xl prose-blockquote:border-l-4 prose-blockquote:border-brand/40 prose-blockquote:bg-muted/30 prose-blockquote:py-1 prose-blockquote:pl-6",
        "prose-img:rounded-xl prose-img:border prose-img:border-border/50 prose-img:shadow-sm prose-img:mx-auto",
        "prose-a:font-semibold prose-a:text-brand prose-a:underline-offset-4 hover:prose-a:underline",
        "prose-code:rounded-md prose-code:bg-muted/80 prose-code:px-1.5 prose-code:py-0.5 prose-code:before:content-none prose-code:after:content-none",
        className
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
    </div>
  );
}
