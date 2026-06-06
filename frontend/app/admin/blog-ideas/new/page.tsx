import Link from "next/link";

import { AdminBackLink } from "@/components/admin/admin-back-link";
import { AdminCard, AdminCardBody } from "@/components/admin/admin-card";
import { AdminFormField, AdminInput, AdminTextarea } from "@/components/admin/admin-form";
import { AdminPageHeader } from "@/components/admin/admin-page-header";
import { adminPageStackClass } from "@/components/admin/admin-ui";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { cn } from "@/lib/utils";
import { createIdeaAction } from "../actions";
import {
  listContextPickerProjects,
  listContextPickerShowcases,
} from "./data";
import { GenerateFromContextForm } from "./generate-from-context-form";
import { IdeaGenerationPoller } from "./idea-generation-poller";

type Props = {
  searchParams: Promise<{
    mode?: string;
    taskId?: string;
    opStatus?: string;
    message?: string;
  }>;
};

export default async function NewBlogIdeaPage({ searchParams }: Props) {
  const params = await searchParams;
  const [projects, showcases] = await Promise.all([
    listContextPickerProjects(),
    listContextPickerShowcases(),
  ]);

  const manualMode = params.mode === "manual";
  const hasContextSources = projects.length > 0 || showcases.length > 0;
  const showGenerate = !manualMode && hasContextSources;

  return (
    <div className={adminPageStackClass}>
      <AdminPageHeader
        description="Generate a blog idea from a project or showcase, or create one manually."
        title="New blog idea"
        actions={<AdminBackLink href="/admin/blog-ideas">Back to ideas</AdminBackLink>}
      />

      <IdeaGenerationPoller opStatus={params.opStatus} taskId={params.taskId} />

      <div className="flex flex-wrap gap-2">
        <Link
          className={cn(
            "rounded-[var(--radius-admin-sm)] border px-3 py-1.5 text-sm transition-colors",
            showGenerate
              ? "border-brand/40 bg-brand/10 text-foreground"
              : "border-border/60 text-muted-foreground hover:text-foreground",
          )}
          href="/admin/blog-ideas/new"
        >
          Generate from context
        </Link>
        <Link
          className={cn(
            "rounded-[var(--radius-admin-sm)] border px-3 py-1.5 text-sm transition-colors",
            manualMode || !hasContextSources
              ? "border-brand/40 bg-brand/10 text-foreground"
              : "border-border/60 text-muted-foreground hover:text-foreground",
          )}
          href="/admin/blog-ideas/new?mode=manual"
        >
          Manual entry
        </Link>
      </div>

      {showGenerate ? (
        <GenerateFromContextForm projects={projects} showcases={showcases} />
      ) : (
        <AdminCard>
          <AdminCardBody>
            {!hasContextSources && !manualMode ? (
              <p className="mb-4 text-sm text-muted-foreground">
                Add a project or showcase first to use AI generation, or switch to manual entry.
              </p>
            ) : null}
            <form action={createIdeaAction} className="grid max-w-2xl gap-5">
              <AdminFormField htmlFor="title" label="Title">
                <AdminInput
                  id="title"
                  name="title"
                  placeholder="e.g. How We Built an AI Evaluation Pipeline"
                  required
                />
              </AdminFormField>

              <AdminFormField htmlFor="angle" label="Angle">
                <AdminInput
                  id="angle"
                  name="angle"
                  placeholder="e.g. AI Engineering, Case Study, Evaluation"
                  required
                />
              </AdminFormField>

              <AdminFormField htmlFor="targetReader" label="Target reader">
                <AdminInput
                  id="targetReader"
                  name="targetReader"
                  placeholder="e.g. CTO, product manager, developer"
                  required
                />
              </AdminFormField>

              <AdminFormField htmlFor="articleGoal" label="Article goal">
                <AdminTextarea
                  id="articleGoal"
                  name="articleGoal"
                  placeholder="What should this article accomplish?"
                  rows={4}
                  required
                />
              </AdminFormField>

              <div className="flex flex-wrap gap-3 pt-2">
                <Button type="submit" variant="brand">
                  Create idea
                </Button>
                <ButtonLink href="/admin/blog-ideas" variant="outline">
                  Cancel
                </ButtonLink>
              </div>
            </form>
          </AdminCardBody>
        </AdminCard>
      )}
    </div>
  );
}
