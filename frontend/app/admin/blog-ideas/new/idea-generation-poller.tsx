"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

import { ButtonLink } from "@/components/ui/button-link";
import { cn } from "@/lib/utils";
import { pollGenerationJobAction, resolveGeneratedIdeaAction } from "../actions";

type Props = {
  taskId?: string;
  opStatus?: string;
};

type BannerState = "polling" | "completed" | "failed" | "idle";

export function IdeaGenerationPoller({ taskId, opStatus }: Props) {
  const polling = useRef(false);
  const [banner, setBanner] = useState<BannerState>("idle");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const startPolling = useCallback(() => {
    if (!taskId || polling.current) return;
    polling.current = true;
    setBanner("polling");
    setErrorMsg(null);

    const abort = new AbortController();
    const { signal } = abort;

    const poll = async () => {
      for (let attempt = 1; attempt <= 60 && !signal.aborted; attempt++) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        if (signal.aborted) return;

        const job = await pollGenerationJobAction(taskId);
        if (signal.aborted) return;

        if (job.status === "failed") {
          setBanner("failed");
          setErrorMsg(job.error_message ?? "Idea generation failed in the worker.");
          polling.current = false;
          return;
        }

        if (job.status === "completed") {
          const ideaId = await resolveGeneratedIdeaAction(taskId);
          if (ideaId) {
            setBanner("completed");
            window.location.href = `/admin/blog-ideas/${ideaId}?opStage=idea&opStatus=completed&message=${encodeURIComponent("Blog idea generated.")}`;
            return;
          }
          setBanner("failed");
          setErrorMsg("Generation completed but the new idea could not be found. Check the ideas list.");
          polling.current = false;
          return;
        }
      }

      setBanner("failed");
      setErrorMsg("Idea generation timed out after 2 minutes.");
      polling.current = false;
    };

    void poll();
    return () => abort.abort();
  }, [taskId]);

  useEffect(() => {
    if (taskId && opStatus === "queued") {
      return startPolling();
    }
    return undefined;
  }, [taskId, opStatus, startPolling]);

  if (banner === "idle") return null;

  return (
    <div
      className={cn(
        "rounded-[var(--radius-admin-sm)] border px-4 py-3 text-sm",
        banner === "polling" && "border-brand/30 bg-brand/5 text-foreground",
        banner === "completed" && "border-emerald-500/30 bg-emerald-500/5",
        banner === "failed" && "border-destructive/30 bg-destructive/5",
      )}
      role="status"
    >
      {banner === "polling" && (
        <p className="flex items-center gap-2">
          <Loader2 className="size-4 animate-spin" aria-hidden />
          Generating blog idea from selected context…
        </p>
      )}
      {banner === "completed" && (
        <p className="flex items-center gap-2 text-emerald-700 dark:text-emerald-400">
          <CheckCircle2 className="size-4" aria-hidden />
          Idea ready — opening detail…
        </p>
      )}
      {banner === "failed" && (
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <p className="flex items-center gap-2 text-destructive">
            <AlertCircle className="size-4 shrink-0" aria-hidden />
            {errorMsg}
          </p>
          <ButtonLink href="/admin/blog-ideas" variant="outline" size="sm">
            Back to ideas
          </ButtonLink>
        </div>
      )}
    </div>
  );
}
