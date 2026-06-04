"use client";

import { useActionState, useEffect, useReducer, useRef, useState } from "react";
import { Globe, Pencil, Save, FileText } from "lucide-react";

import type { ProjectEditorActionState } from "@/app/admin/projects/editor/actions";
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

type ProjectEditorProps = {
  initialContentMarkdown?: string;
  initialDescription?: string;
  initialImageUrl?: string;
  initialProjectId?: string;
  initialSlug?: string;
  initialTitle?: string;
  publishAction: (
    previous: ProjectEditorActionState,
    formData: FormData
  ) => Promise<ProjectEditorActionState>;
  saveDraftAction: (
    previous: ProjectEditorActionState,
    formData: FormData
  ) => Promise<ProjectEditorActionState>;
};

const initialActionState: ProjectEditorActionState = {
  message: "Ready",
  projectId: "",
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
  }
}

export function ProjectEditor({
  initialContentMarkdown = "",
  initialDescription = "",
  initialImageUrl = "",
  initialProjectId = "",
  initialSlug,
  initialTitle = "New Project",
  publishAction,
  saveDraftAction,
}: ProjectEditorProps) {
  const [saveState, saveFormAction] = useActionState(saveDraftAction, {
    ...initialActionState,
    projectId: initialProjectId,
  });
  const [publishState, publishFormAction] = useActionState(publishAction, {
    ...initialActionState,
    projectId: initialProjectId,
  });
  const visibleState = publishState.status !== "idle" ? publishState : saveState;

  const [slugState, dispatchSlug] = useReducer(slugReducer, {
    slug: initialSlug ?? slugify(initialTitle),
    showEditor: false,
    manuallyEdited: false,
  });

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

  const publishStatusRef = useRef(publishState.status);
  useEffect(() => {
    if (publishState.status === "published" && publishStatusRef.current !== "published") {
      publishStatusRef.current = "published";
      const timeout = setTimeout(() => {
        window.location.href = "/projects";
      }, 1500);
      return () => clearTimeout(timeout);
    }
    publishStatusRef.current = publishState.status;
  }, [publishState.status]);

  return (
    <form action={saveFormAction} className={adminEditorGridClass}>
      <input name="projectId" type="hidden" value={visibleState.projectId} />
      <input name="slug" type="hidden" value={slugState.slug} />
      <input name="contentMarkdown" type="hidden" value={contentMarkdown} />
      <input name="imageUrl" type="hidden" value={imageUrl} />

      <AdminCard>
        <AdminCardSection title="Project content" />
        <AdminCardBody className={adminEditorFieldsClass}>
          <AdminFormField htmlFor="project-title" label="Title">
            <AdminInput
              id="project-title"
              name="title"
              defaultValue={initialTitle}
              onChange={handleTitleChange}
              placeholder="Enter project title..."
            />
          </AdminFormField>

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
                {slugState.showEditor ? "Hide URL" : `URL: /projects/${slugState.slug}`}
              </span>
            </button>

            {slugState.showEditor && (
              <div className="mt-2 flex items-center gap-2">
                <span className="shrink-0 text-xs text-muted-foreground">/projects/</span>
                <AdminInput
                  id="project-slug"
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

          <AdminFormField className="md:col-span-2" htmlFor="project-description" label="Description">
            <AdminTextarea
              id="project-description"
              name="description"
              defaultValue={initialDescription}
              placeholder="Short project description..."
            />
          </AdminFormField>

          <AdminFormField htmlFor="project-image-url" label="Image URL">
            <AdminInput
              id="project-image-url"
              name="image-url"
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="https://example.com/image.jpg"
              type="url"
            />
          </AdminFormField>
        </AdminCardBody>

        <AdminEditorDivider />

        <AdminCardSection title="Project body" />
        <AdminCardBody>
          <AdminMinimalTiptap value={contentMarkdown} onChange={setContentMarkdown} />
        </AdminCardBody>
      </AdminCard>

      <AdminWorkflowCard
        description="Save a draft or publish this project for the public site."
        title="Project actions"
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
          <span className="truncate">{visibleState.message}</span>
        </div>

        <AdminEditorDivider />
          <PendingSubmitButton
            formAction={saveFormAction}
            pendingLabel="Saving…"
            variant="secondary"
          >
            <Save className="size-3.5" aria-hidden />
            Save draft
          </PendingSubmitButton>

          <PendingSubmitButton
            formAction={publishFormAction}
            pendingLabel="Publishing…"
          >
            <Globe className="size-3.5" aria-hidden />
            Publish
          </PendingSubmitButton>
        </AdminWorkflowCard>
    </form>
  );
}
