"use client";

import Link from "next/link";
import { useActionState } from "react";

import { PublicBackLink } from "@/components/public/public-back-link";
import { PublicPageShell } from "@/components/public/public-page-shell";
import { publicMainWidthClass } from "@/components/public/public-ui";
import { cn } from "@/lib/utils";

import { submitAiNewsLinkAction, type SubmitLinkState } from "./actions";

const initialState: SubmitLinkState | null = null;

export function AiNewsSubmitForm() {
  const [state, formAction, pending] = useActionState(submitAiNewsLinkAction, initialState);

  return (
    <PublicPageShell currentPath="/ai-news">
      <section className={cn(publicMainWidthClass, "flex flex-col gap-10 sm:gap-12")}>
        <PublicBackLink href="/ai-news">AI News</PublicBackLink>

        <div className="flex flex-col gap-4">
          <p className="text-sm uppercase tracking-[0.2em] text-muted-foreground">Submit a link</p>
          <h1 className="font-display text-4xl font-medium tracking-tight sm:text-5xl">
            Suggest AI news for review
          </h1>
          <p className="max-w-2xl text-muted-foreground">
            Share an AI-related article or announcement. Submissions are validated, deduplicated, and
            reviewed by the AI Lab team before anything appears on the public feed.
          </p>
        </div>

        <form action={formAction} className="flex max-w-xl flex-col gap-5">
          <label className="flex flex-col gap-2 text-sm">
            URL *
            <input
              required
              className="rounded-md border bg-background px-3 py-2"
              name="url"
              placeholder="https://example.com/ai-announcement"
              type="url"
            />
          </label>

          <label className="flex flex-col gap-2 text-sm">
            Your name
            <input className="rounded-md border bg-background px-3 py-2" name="name" type="text" />
          </label>

          <label className="flex flex-col gap-2 text-sm">
            Email
            <input className="rounded-md border bg-background px-3 py-2" name="email" type="email" />
          </label>

          <label className="flex flex-col gap-2 text-sm">
            Why is this worth reading?
            <textarea className="min-h-24 rounded-md border bg-background px-3 py-2" name="note" />
          </label>

          <label className="flex flex-col gap-2 text-sm">
            Suggested category
            <input className="rounded-md border bg-background px-3 py-2" name="category" type="text" />
          </label>

          <button
            className="inline-flex w-fit rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-60"
            disabled={pending}
            type="submit"
          >
            {pending ? "Submitting…" : "Submit link"}
          </button>

          {state ? (
            <p className={cn("text-sm", state.ok ? "text-emerald-700" : "text-destructive")}>{state.message}</p>
          ) : null}
        </form>

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
