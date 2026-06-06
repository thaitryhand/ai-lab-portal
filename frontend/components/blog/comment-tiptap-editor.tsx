"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { Editor } from "@tiptap/react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import LinkExtension from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";
import {
  Bold,
  Italic,
  Strikethrough,
  Code,
  Quote,
  List,
  ListOrdered,
  Heading3,
  Link,
  Undo,
  Redo,
} from "lucide-react";

import { Avatar } from "@/components/public/public-avatar";
import { cn } from "@/lib/utils";

type CommentTiptapEditorProps = {
  onSubmit: (content: string) => void;
  placeholder?: string;
  autoFocus?: boolean;
  onCancel?: () => void;
  isSubmitting?: boolean;
  session?: {
    user: { id: string; name?: string; email: string; image?: string | null };
  } | null;
  /** Pre‑fill the editor with existing HTML content (edit mode). */
  initialContent?: string;
};

type ToolbarAction = {
  key: string;
  icon: typeof Bold;
  label: string;
  action: (editor: Editor) => void;
  isActive: (editor: Editor) => boolean;
};

function createToolbar(): ToolbarAction[] {
  return [
    {
      key: "bold",
      icon: Bold,
      label: "Bold",
      action: (e) => e.chain().focus().toggleBold().run(),
      isActive: (e) => e.isActive("bold"),
    },
    {
      key: "italic",
      icon: Italic,
      label: "Italic",
      action: (e) => e.chain().focus().toggleItalic().run(),
      isActive: (e) => e.isActive("italic"),
    },
    {
      key: "strikethrough",
      icon: Strikethrough,
      label: "Strikethrough",
      action: (e) => e.chain().focus().toggleStrike().run(),
      isActive: (e) => e.isActive("strike"),
    },
    {
      key: "code",
      icon: Code,
      label: "Code",
      action: (e) => e.chain().focus().toggleCode().run(),
      isActive: (e) => e.isActive("code"),
    },
    {
      key: "heading",
      icon: Heading3,
      label: "Heading",
      action: (e) => e.chain().focus().toggleHeading({ level: 3 }).run(),
      isActive: (e) => e.isActive("heading", { level: 3 }),
    },
    {
      key: "blockquote",
      icon: Quote,
      label: "Blockquote",
      action: (e) => e.chain().focus().toggleBlockquote().run(),
      isActive: (e) => e.isActive("blockquote"),
    },
    {
      key: "bulletList",
      icon: List,
      label: "Bullet list",
      action: (e) => e.chain().focus().toggleBulletList().run(),
      isActive: (e) => e.isActive("bulletList"),
    },
    {
      key: "orderedList",
      icon: ListOrdered,
      label: "Numbered list",
      action: (e) => e.chain().focus().toggleOrderedList().run(),
      isActive: (e) => e.isActive("orderedList"),
    },
    {
      key: "link",
      icon: Link,
      label: "Link",
      action: (e) => {
        const prev = e.isActive("link") ? e.getAttributes("link").href : "";
        const url = window.prompt("Enter URL", prev || "https://");
        if (url === null) return;
        if (!url) {
          e.chain().focus().unsetLink().run();
          return;
        }
        e.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
      },
      isActive: (e) => e.isActive("link"),
    },
  ];
}

const TOOLBAR_ACTIONS = createToolbar();
const MAX_CHARS = 10000;

export function CommentTiptapEditor({
  onSubmit,
  placeholder = "Share your thoughts...",
  autoFocus,
  onCancel,
  isSubmitting: externalSubmitting,
  session,
  initialContent,
}: CommentTiptapEditorProps) {
  const [hasContent, setHasContent] = useState(
    initialContent
      ? initialContent.replace(/<[^>]*>/g, "").trim().length > 0
      : false,
  );
  const [charCount, setCharCount] = useState(
    initialContent ? initialContent.replace(/<[^>]*>/g, "").length : 0,
  );
  const [isSubmittingInternal, setIsSubmittingInternal] = useState(false);

  // ── Refs for values passed to editorProps (avoid stale closures) ──
  const onSubmitRef = useRef(onSubmit);
  const submitLockRef = useRef(false);
  const editorRef = useRef<ReturnType<typeof useEditor>>(null);
  const handleSubmitRef = useRef<() => Promise<void>>(async () => {});
  const externalSubmittingRef = useRef(externalSubmitting);
  const isBusy = Boolean(externalSubmitting) || isSubmittingInternal;

  const editor = useEditor({
    content: initialContent,
    extensions: [
      StarterKit.configure({
        heading: { levels: [3] },
        codeBlock: false,
        horizontalRule: false,
        link: false,
      }),
      LinkExtension.configure({
        openOnClick: false,
        HTMLAttributes: {
          class: "text-brand underline underline-offset-2 hover:text-brand/80",
        },
      }),
      Placeholder.configure({ placeholder, showOnlyWhenEditable: false }),
    ],
    editorProps: {
      attributes: {
        class:
          "comment-tiptap focus:outline-none text-sm leading-7 text-foreground px-6 py-5",
      },
      handleKeyDown: (view, event) => {
        // Meta/Ctrl+Enter → submit
        if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
          event.preventDefault();
          handleSubmitRef.current();
          return true;
        }
        return false;
      },
    },
    autofocus: autoFocus ? "end" : false,
    immediatelyRender: true,
    onUpdate: ({ editor }) => {
      const text = editor.state.doc.textContent;
      const len = text.length;
      if (len > MAX_CHARS) {
        editor.commands.setContent(editor.state.doc.cut(0, MAX_CHARS));
        return;
      }
      setHasContent(text.trim().length > 0);
      setCharCount(len);
    },
  });

  useEffect(() => {
    onSubmitRef.current = onSubmit;
  }, [onSubmit]);

  useEffect(() => {
    externalSubmittingRef.current = externalSubmitting;
  }, [externalSubmitting]);

  const handleSubmit = useCallback(async () => {
    const ed = editorRef.current;
    if (!ed || submitLockRef.current || externalSubmittingRef.current) return;
    const text = ed.state.doc.textContent.trim();
    if (!text) return;

    submitLockRef.current = true;
    setIsSubmittingInternal(true);
    try {
      const html = ed.getHTML();
      await onSubmitRef.current(html);
      ed.commands.clearContent(true);
      setHasContent(false);
      setCharCount(0);
    } finally {
      submitLockRef.current = false;
      setIsSubmittingInternal(false);
    }
  }, []);

  useEffect(() => {
    editorRef.current = editor;
    handleSubmitRef.current = handleSubmit;
  }, [editor, handleSubmit]);

  const handleToolbarAction = useCallback(
    (action: ToolbarAction) => {
      if (!editor) return;
      action.action(editor);
      editor.chain().focus().run();
    },
    [editor],
  );

  const userName = session?.user?.name || session?.user?.email || "You";
  const canSubmit = hasContent && !isBusy;

  return (
    <div className="flex gap-4">
      {/* Avatar — always stays fixed, never scrolls */}
      <div className="mt-0.5 shrink-0 self-start">
        <Avatar src={session?.user?.image} name={userName} size="md" />
      </div>

      {/* Editor column */}
      <div className="min-w-0 flex-1 flex flex-col">
        {/* Toolbar + Editor container */}
        <div
          className={cn(
            "overflow-hidden rounded-2xl border border-border/80 bg-card shadow-sm transition-all",
            "focus-within:border-brand/40 focus-within:shadow-[0_0_0_3px] focus-within:shadow-brand/10",
          )}
        >
          {/* Toolbar */}
          <div className="flex items-center flex-wrap gap-0.5 border-b border-border/50 bg-muted/30 px-3 py-2">
            {TOOLBAR_ACTIONS.map((action) => {
              const active = editor ? action.isActive(editor) : false;
              return (
                <button
                  key={action.key}
                  type="button"
                  onClick={() => handleToolbarAction(action)}
                  className={cn(
                    "flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-all hover:bg-background hover:text-foreground active:scale-95",
                    active && "bg-background text-foreground shadow-sm",
                  )}
                  title={action.label}
                  aria-label={action.label}
                  aria-pressed={active}
                  tabIndex={-1}
                >
                  <action.icon className="size-4.5" />
                </button>
              );
            })}
            <span className="ml-auto flex items-center gap-0.5">
              <button
                type="button"
                onClick={() => editor?.chain().focus().undo().run()}
                disabled={!editor?.can().undo()}
                className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-all hover:bg-background hover:text-foreground active:scale-95 disabled:opacity-30 disabled:pointer-events-none"
                title="Undo"
                tabIndex={-1}
              >
                <Undo className="size-4.5" />
              </button>
              <button
                type="button"
                onClick={() => editor?.chain().focus().redo().run()}
                disabled={!editor?.can().redo()}
                className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-all hover:bg-background hover:text-foreground active:scale-95 disabled:opacity-30 disabled:pointer-events-none"
                title="Redo"
                tabIndex={-1}
              >
                <Redo className="size-4.5" />
              </button>
            </span>
          </div>

          {/* Scrollable editor area */}
          <div className="max-h-90 overflow-y-auto comment-tiptap">
            <EditorContent editor={editor} />
          </div>
        </div>

        {/* Footer */}
        <div className="mt-3 flex items-center justify-between px-0.5">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => handleSubmitRef.current()}
              disabled={!canSubmit}
              className={cn(
                "inline-flex items-center gap-2 rounded-full px-5 py-2 text-sm font-medium transition-all",
                canSubmit
                  ? "bg-brand text-brand-foreground shadow-sm hover:opacity-90 active:scale-[0.97]"
                  : "bg-muted text-muted-foreground/60 cursor-not-allowed",
              )}
            >
              {isBusy ? (
                <>
                  <span className="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Posting...
                </>
              ) : (
                "Submit"
              )}
            </button>
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                Cancel
              </button>
            )}
          </div>

          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <span
              className={cn(
                charCount > MAX_CHARS * 0.85 && "text-amber-500",
                charCount >= MAX_CHARS && "text-destructive",
              )}
            >
              {charCount}/{MAX_CHARS}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
