"use client";

import dynamic from "next/dynamic";

import { adminTiptapShellClass } from "@/components/admin/admin-ui";
import { cn } from "@/lib/utils";

const MinimalTiptapEditor = dynamic(
  () =>
    import("@/components/ui/minimal-tiptap").then((module) => ({
      default: module.MinimalTiptapEditor,
    })),
  {
    loading: () => (
      <div
        aria-hidden
        className="min-h-88 animate-pulse rounded-lg border border-border bg-muted/30"
      />
    ),
    ssr: false,
  }
);

type AdminMinimalTiptapProps = {
  className?: string;
  onChange: (markdown: string) => void;
  placeholder?: string;
  value: string;
  /** Custom function to upload image files. Defaults to server-side /api/upload/image. */
  uploader?: (file: File) => Promise<string>;
};

export function AdminMinimalTiptap({
  className,
  onChange,
  placeholder = "Write your content…",
  value,
  uploader,
}: AdminMinimalTiptapProps) {
  return (
    <MinimalTiptapEditor
      className={cn(adminTiptapShellClass, "w-full", className)}
      editable
      editorClassName="min-h-72 px-0"
      editorContentClassName="px-4 py-3.5 text-[15px] leading-7 text-foreground"
      onChange={(content) => {
        if (typeof content === "string") {
          onChange(content);
        }
      }}
      output="markdown"
      placeholder={placeholder}
      throttleDelay={200}
      uploader={uploader}
      value={value}
    />
  );
}
