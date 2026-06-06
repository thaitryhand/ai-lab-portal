"use client";

import Link from "next/link";
import { useActionState } from "react";

import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageHero } from "@/components/public/public-page-hero";
import { PublicPageShell } from "@/components/public/public-page-shell";
import {
  publicEyebrowClass,
  publicMainWidthClass,
  publicPanelPaddingClass,
} from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

import { submitAiNewsLinkAction, type SubmitLinkState } from "./actions";

const initialState: SubmitLinkState | null = null;

export function AiNewsSubmitForm() {
  const [state, formAction, pending] = useActionState(submitAiNewsLinkAction, initialState);

  return (
      <PublicPageShell currentPath="/ai-news">
        <section className={cn(publicMainWidthClass, "flex flex-col gap-12 sm:gap-14")}>
          <PublicBackLink href="/ai-news">AI News</PublicBackLink>

          <PublicPageHero
            description="Share an AI-related article or announcement. Submissions are validated, deduplicated, and reviewed by the AI Lab team before anything appears on the public feed."
            eyebrow="Submit a link"
            title="Suggest AI news for review."
          />

          <div className="grid gap-8 lg:grid-cols-[0.88fr_1.12fr] lg:items-start lg:gap-12">
            <aside className={cn("rounded-[1.5rem] border border-border/80 bg-card/80", publicPanelPaddingClass)}>
              <p className={publicEyebrowClass}>Review criteria</p>
              <div className="mt-8 grid gap-5 text-sm leading-7 text-muted-foreground">
                <p>Prefer primary sources, release notes, research posts, and announcements with clear product or technical impact.</p>
                <p>Skip thin summaries, copied social posts, and articles without a stable original URL.</p>
              </div>
            </aside>

            <form action={formAction} className={cn("flex flex-col gap-5 rounded-[1.5rem] border border-border/80 bg-card/90", publicPanelPaddingClass)}>
              <label className="flex flex-col gap-2 text-sm font-medium text-foreground">
                URL *
                <input
                  required
                  className="h-11 rounded-xl border border-border/80 bg-background px-4 text-sm outline-none transition-colors focus:border-brand/50"
                  name="url"
                  placeholder="https://example.com/ai-announcement"
                  type="url"
                />
              </label>

              <div className="grid gap-5 sm:grid-cols-2">
                <label className="flex flex-col gap-2 text-sm font-medium text-foreground">
                  Your name
                  <input className="h-11 rounded-xl border border-border/80 bg-background px-4 text-sm outline-none transition-colors focus:border-brand/50" name="name" type="text" />
                </label>

                <label className="flex flex-col gap-2 text-sm font-medium text-foreground">
                  Email
                  <input className="h-11 rounded-xl border border-border/80 bg-background px-4 text-sm outline-none transition-colors focus:border-brand/50" name="email" type="email" />
                </label>
              </div>

              <label className="flex flex-col gap-2 text-sm font-medium text-foreground">
                Why is this worth reading?
                <textarea className="min-h-28 rounded-xl border border-border/80 bg-background px-4 py-3 text-sm outline-none transition-colors focus:border-brand/50" name="note" />
              </label>

              <label className="flex flex-col gap-2 text-sm font-medium text-foreground">
                Suggested category
                <input className="h-11 rounded-xl border border-border/80 bg-background px-4 text-sm outline-none transition-colors focus:border-brand/50" name="category" type="text" />
              </label>

              <button
                className="inline-flex h-11 w-fit items-center justify-center rounded-full bg-primary px-6 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/92 disabled:opacity-60"
                disabled={pending}
                type="submit"
              >
                {pending ? "Submitting..." : "Submit link"}
              </button>

              {state ? (
                <p className={cn("rounded-xl border px-4 py-3 text-sm", state.ok ? "border-brand/20 bg-accent text-brand" : "border-destructive/20 bg-destructive/10 text-destructive")}>{state.message}</p>
              ) : null}
            </form>
          </div>

          <p className="text-sm text-muted-foreground">
            Already published items appear on{" "}
            <Link className="underline underline-offset-4" href="/ai-news">
            /ai-news
          </Link>
          .
        </p>
      </section>
    </PublicPageShell>
  );
}
