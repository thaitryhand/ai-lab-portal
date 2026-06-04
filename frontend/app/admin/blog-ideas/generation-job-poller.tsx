"use client";

import { useEffect, useRef } from "react";

import { pollGenerationJobAction } from "./actions";

type Props = {
  ideaId: string;
  taskId?: string;
  opStatus?: string;
};

export function GenerationJobPoller({ ideaId, taskId, opStatus }: Props) {
  const polling = useRef(false);

  useEffect(() => {
    if (!taskId || opStatus !== "queued" || polling.current) return;
    polling.current = true;

    const abort = new AbortController();
    const { signal } = abort;

    const poll = async () => {
      for (let attempt = 0; attempt < 60 && !signal.aborted; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 2000));
        if (signal.aborted) return;
        const job = await pollGenerationJobAction(taskId);
        if (job.status === "completed") {
          window.location.reload();
          return;
        }
        if (job.status === "failed") {
          const params = new URLSearchParams({
            opStage: job.stage,
            opStatus: "error",
            message: job.error_message ?? "Generation failed in the worker.",
          });
          window.location.href = `/admin/blog-ideas/${ideaId}?${params.toString()}`;
          return;
        }
      }
    };

    void poll();
    return () => abort.abort();
  }, [ideaId, taskId, opStatus]);

  return null;
}
