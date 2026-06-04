"use client";

import { useActionState, useEffect, useReducer, useRef, useState } from "react";
import { Globe, Pencil, Save, FileText } from "lucide-react";

import { AdminCard, AdminCardBody, AdminCardSection, AdminWorkflowCard } from "@/components/admin/admin-card";
import { AdminFormField, AdminInput, AdminTextarea } from "@/components/admin/admin-form";
import { AdminMinimalTiptap } from "@/components/admin/admin-minimal-tiptap";
import { AdminEditorDivider } from "@/components/admin/admin-editor-divider";
import {
  adminEditorFieldsClass,
  adminEditorGridClass,
  adminStatusPanelClass,
  adminWorkflowStatusClass,
} from "@/components/admin/admin-ui";
import { PendingSubmitButton } from "@/components/admin/pending-submit-button";
import { cn } from "@/lib/utils";

import type { EditorActionState } from "../../app/admin/blog/editor/actions";

type BlogEditorProps = {
  initialAuthorName?: string;
  initialContentMarkdown?: string;
  initialExcerpt?: string;
  initialImageUrl?: string;
  initialPostId?: string;
  initialSlug?: string;
  initialTitle?: string;
  saveDraftAction: (previous: EditorActionState, formData: FormData) => Promise<EditorActionState>;
  publishAction: (previous: EditorActionState, formData: FormData) => Promise<EditorActionState>;
};

const initialActionState: EditorActionState = {
  message: "Ready",
  postId: "",
  status: "idle",
};

function slugify(text: string): string {
  return (
    text
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, "")
      .replace(/[\s_]+/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 80) || "untitled"
  );
}

type SlugState = {
  slug: string;
  showEditor: boolean;
  manuallyEdited: boolean;
};

type SlugAction =
  | { type: "init"; slug: string }
  | { type: "title_changed"; title: string }
  | { type: "manual_edit"; value: string }
  | { type: "toggle_editor" }
  | { type: "reset"; title: string };

function slugReducer(state: SlugState, action: SlugAction): SlugState {
  switch (action.type) {
    case "init":
      return { slug: action.slug, showEditor: false, manuallyEdited: false };
    case "title_changed":
      if (state.manuallyEdited) return state;
      return { ...state, slug: slugify(action.title) };
    case "manual_edit":
      return { ...state, slug: action.value, manuallyEdited: true };
    case "toggle_editor":
      return { ...state, showEditor: !state.showEditor };
    case "reset":
      return { slug: slugify(action.title), showEditor: false, manuallyEdited: false };
    default:
      return state;
  }
}

const SAVED_INDICATOR_DELAY_MS = 1_500;

export function BlogEditor({
  initialAuthorName = "AI Lab Team",
  initialContentMarkdown = "",
  initialExcerpt = "A practical draft about pairing AI assistance with human approval, evidence, and measurable workflow design.",
  initialImageUrl = "",
  initialPostId = "",
  initialSlug,
  initialTitle = "Building useful AI agents without losing review control",
  saveDraftAction,
  publishAction,
}: BlogEditorProps) {
  const [saveState, saveFormAction] = useActionState(saveDraftAction, {
    ...initialActionState,
    postId: initialPostId,
  });
  const [publishState, publishFormAction] = useActionState(publishAction, {
    ...initialActionState,
    postId: initialPostId,
  });
  const visibleState = publishState.status !== "idle" ? publishState : saveState;

  // Slug state managed via reducer (replaces 3 separate useState)
  const [slugState, dispatchSlug] = useReducer(slugReducer, {
    slug: initialSlug ?? slugify(initialTitle),
    showEditor: false,
    manuallyEdited: false,
  });

  // Title changes tracked via ref (never displayed, only used for slug generation)
  const titleRef = useRef(initialTitle);
  const titleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newTitle = e.target.value;
    titleRef.current = newTitle;
    if (titleTimerRef.current) clearTimeout(titleTimerRef.current);
    titleTimerRef.current = setTimeout(() => {
      dispatchSlug({ type: "title_changed", title: newTitle });
    }, 300);
  };

  const [contentMarkdown, setContentMarkdown] = useState(initialContentMarkdown);
  const [imageUrl, setImageUrl] = useState(initialImageUrl);

  // Redirect to blog listing after successful publish
  const publishStatusRef = useRef(publishState.status);
  useEffect(() => {
    if (publishState.status === "published" && publishStatusRef.current !== "published") {
      publishStatusRef.current = "published";
      const timeout = setTimeout(() => {
        window.location.href = "/blog";
      }, SAVED_INDICATOR_DELAY_MS);
      return () => clearTimeout(timeout);
    }
    publishStatusRef.current = publishState.status;
  }, [publishState.status]);

  return (
    <form action={saveFormAction} className={adminEditorGridClass}>
      <input name="postId" type="hidden" value={visibleState.postId} />
      <input name="authorName" type="hidden" value={initialAuthorName} />
      <input name="slug" type="hidden" value={slugState.slug} />
      <input name="contentMarkdown" type="hidden" value={contentMarkdown} />
      <input name="imageUrl" type="hidden" value={imageUrl} />

      <AdminCard>
        <AdminCardSection title="Metadata" />
        <AdminCardBody className={adminEditorFieldsClass}>
          <AdminFormField htmlFor="blog-title" label="Title">
            <AdminInput
              id="blog-title"
              name="title"
              defaultValue={initialTitle}
              onChange={handleTitleChange}
              placeholder="Enter your post title..."
            />
          </AdminFormField>

          {/* Slug — auto-generated, collapsible editor */}
          <div className="md:col-span-2 -mt-1">
            <button
              type="button"
              onClick={() => dispatchSlug({ type: "toggle_editor" })}
              className={cn(
                "inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors",
                "hover:text-foreground"
              )}
            >
              <Pencil className="size-3" />
              <span>
                {slugState.showEditor ? "Hide URL" : `URL: /blog/${slugState.slug}`}
              </span>
            </button>

            {slugState.showEditor && (
              <div className="mt-2 flex items-center gap-2">
                <span className="shrink-0 text-xs text-muted-foreground">/blog/</span>
                <AdminInput
                  id="blog-slug"
                  name="slug-editor"
                  value={slugState.slug}
                  onChange={(e) => dispatchSlug({ type: "manual_edit", value: e.target.value })}
                  className="h-8 text-xs"
                  placeholder="url-slug"
                />
                {slugState.manuallyEdited && (
                  <button
                    type="button"
                    onClick={() => dispatchSlug({ type: "reset", title: titleRef.current })}
                    className="shrink-0 text-xs text-muted-foreground underline underline-offset-2 hover:text-foreground"
                  >
                    Reset
                  </button>
                )}
              </div>
            )}
          </div>

          <AdminFormField className="md:col-span-2" htmlFor="blog-excerpt" label="Excerpt">
            <AdminTextarea id="blog-excerpt" name="excerpt" defaultValue={initialExcerpt} rows={3} />
          </AdminFormField>

          <AdminFormField className="md:col-span-2" htmlFor="blog-image-url" label="Featured image URL">
            <AdminInput
              id="blog-image-url"
              name="featured-image-url"
              defaultValue={initialImageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="https://example.com/hero-image.jpg"
            />
          </AdminFormField>
        </AdminCardBody>

        <AdminCardSection
          description="Rich text is saved as Markdown so formatting persists on publish."
          title="Article content"
        />
        <AdminCardBody>
          <AdminMinimalTiptap
            onChange={setContentMarkdown}
            placeholder="Draft your article… Use the toolbar for headings, lists, links, and more."
            value={contentMarkdown}
          />
        </AdminCardBody>
      </AdminCard>

      <AdminWorkflowCard
        description="Save and publish use a server action so the admin boundary secret never reaches the browser."
        title="Draft controls"
      >
        <div
          className={cn(adminWorkflowStatusClass, adminStatusPanelClass(visibleState.status))}
          role="status"
        >
          {visibleState.status === "published" ? (
            <Globe className="size-4 shrink-0 text-brand" />
          ) : visibleState.status === "error" ? (
            <span className="h-2 w-2 shrink-0 rounded-full bg-destructive" aria-hidden />
          ) : (
            <FileText className="size-4 shrink-0 text-muted-foreground" />
          )}
          <span className="truncate">{visibleState.status === "published" ? "Published — redirecting to blog..." : visibleState.message}</span>
        </div>

        <AdminEditorDivider />

        <p className="text-xs leading-relaxed text-muted-foreground">Keep this tab open until the status updates.</p>

        <PendingSubmitButton pendingLabel="Saving draft...">
          <Save className="size-4 shrink-0" />
          Save draft
        </PendingSubmitButton>

        <PendingSubmitButton formAction={publishFormAction} pendingLabel="Publishing..." variant="outline">
          <Globe className="size-4 shrink-0" />
          Publish saved post
        </PendingSubmitButton>
      </AdminWorkflowCard>
    </form>
  );
}
