"use client";

import { useMemo, useState } from "react";
import { useFormStatus } from "react-dom";
import { Sparkles } from "lucide-react";

import { AdminCard, AdminCardBody } from "@/components/admin/admin-card";
import { AdminFormField } from "@/components/admin/admin-form";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { cn } from "@/lib/utils";
import type { ContextPickerItem } from "./data";
import { generateFromContextAction } from "../actions";

type SourceType = "project" | "showcase";

type Props = {
  projects: ContextPickerItem[];
  showcases: ContextPickerItem[];
};

const selectClassName =
  "flex h-10 w-full rounded-[var(--radius-admin-sm)] border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50";

function statusLabel(status: ContextPickerItem["status"]) {
  return status === "published" ? "Published" : "Draft";
}

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <Button disabled={pending} type="submit" variant="brand">
      <Sparkles className="size-4" aria-hidden />
      {pending ? "Generating…" : "Generate idea"}
    </Button>
  );
}

export function GenerateFromContextForm({ projects, showcases }: Props) {
  const defaultSource: SourceType = projects.length > 0 ? "project" : "showcase";
  const [sourceType, setSourceType] = useState<SourceType>(defaultSource);

  const items = sourceType === "project" ? projects : showcases;
  const defaultItemId = items[0]?.id ?? "";

  const emptyMessage =
    sourceType === "project"
      ? "No projects yet. Create a project first, then generate a blog idea from it."
      : "No showcases yet. Create a showcase first, then generate a blog idea from it.";

  const createHref =
    sourceType === "project" ? "/admin/projects/editor" : "/admin/showcases/editor";

  const previewHint = useMemo(() => {
    if (sourceType === "project") {
      return "Uses project title, description, and markdown body as LLM context.";
    }
    return "Uses showcase title, hero summary, industry/use case, and markdown body.";
  }, [sourceType]);

  return (
    <AdminCard>
      <AdminCardBody>
        <div className="mb-5 flex flex-wrap gap-2">
          <button
            type="button"
            className={cn(
              "rounded-[var(--radius-admin-sm)] border px-3 py-1.5 text-sm transition-colors",
              sourceType === "project"
                ? "border-brand/40 bg-brand/10 text-foreground"
                : "border-border/60 text-muted-foreground hover:text-foreground",
            )}
            onClick={() => setSourceType("project")}
          >
            Project
          </button>
          <button
            type="button"
            className={cn(
              "rounded-[var(--radius-admin-sm)] border px-3 py-1.5 text-sm transition-colors",
              sourceType === "showcase"
                ? "border-brand/40 bg-brand/10 text-foreground"
                : "border-border/60 text-muted-foreground hover:text-foreground",
            )}
            onClick={() => setSourceType("showcase")}
          >
            Showcase
          </button>
        </div>

        {items.length === 0 ? (
          <div className="grid max-w-2xl gap-4">
            <p className="text-sm text-muted-foreground">{emptyMessage}</p>
            <ButtonLink href={createHref} variant="outline">
              Create {sourceType}
            </ButtonLink>
          </div>
        ) : (
          <form action={generateFromContextAction} className="grid max-w-2xl gap-5">
            <input type="hidden" name="sourceType" value={sourceType} />

            <AdminFormField
              hint={previewHint}
              htmlFor="contextId"
              label={sourceType === "project" ? "Project" : "Showcase"}
            >
              <select
                key={sourceType}
                className={selectClassName}
                defaultValue={defaultItemId}
                id="contextId"
                name="contextId"
                required
              >
                {items.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.title} ({statusLabel(item.status)})
                  </option>
                ))}
              </select>
            </AdminFormField>

            <div className="flex flex-wrap gap-3 pt-2">
              <SubmitButton />
              <ButtonLink href="/admin/blog-ideas" variant="outline">
                Cancel
              </ButtonLink>
            </div>
          </form>
        )}
      </AdminCardBody>
    </AdminCard>
  );
}
