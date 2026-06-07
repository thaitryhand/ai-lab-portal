"use client";

import { useCallback, useRef, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Props = {
  /** The pipeline stage to stream-generate (outline, draft, review, marketing). */
  stage: "outline" | "draft" | "review" | "marketing";
  /** The blog idea ID. */
  ideaId: string;
  /** Optional label override. */
  label?: string;
};

type Status = "idle" | "connecting" | "streaming" | "done" | "error";

export function StageStreamButton({ stage, ideaId, label }: Props) {
  const router = useRouter();
  const [status, setStatus] = useState<Status>("idle");
  const [tokens, setTokens] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const panelRef = useRef<HTMLDivElement | null>(null);

  const startStream = useCallback(async () => {
    setStatus("connecting");
    setTokens([]);
    setErrorMessage(null);

    try {
      const controller = new AbortController();
      abortRef.current = controller;

      const response = await fetch(
        `/api/admin/blog-ideas/generate-stream/${stage}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ideaId }),
          signal: controller.signal,
        },
      );

      if (!response.ok) {
        setErrorMessage(`HTTP ${response.status}`);
        setStatus("error");
        return;
      }

      setStatus("streaming");

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          try {
            const event = JSON.parse(raw);

            switch (event.type) {
              case "token":
                setTokens((prev) => [...prev, event.data]);
                break;
              case "saved":
                setStatus("done");
                router.refresh();
                return;
              case "error":
                setErrorMessage(event.data ?? "Generation failed");
                setStatus("error");
                return;
            }
          } catch {
            // skip malformed events
          }
        }
      }

      setStatus("done");
      router.refresh();
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setStatus("idle");
        return;
      }
      setErrorMessage(err instanceof Error ? err.message : "Unknown error");
      setStatus("error");
    }
  }, [stage, ideaId, router]);

  const isActive = status === "connecting" || status === "streaming";

  if (isActive || tokens.length > 0 || errorMessage) {
    return (
      <div ref={panelRef} className="mt-3 space-y-2">
        {isActive ? (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="size-3 animate-spin" />
            <span>Streaming {stage}...</span>
          </div>
        ) : null}

        {tokens.length > 0 ? (
          <div
            className={cn(
              "max-h-32 overflow-y-auto rounded-lg border border-border/70 bg-muted/30 p-3",
              "text-xs leading-relaxed text-foreground whitespace-pre-wrap",
            )}
          >
            {tokens.join("")}
            {isActive ? (
              <span className="inline-block w-1 h-3 ml-0.5 bg-brand animate-pulse" />
            ) : null}
          </div>
        ) : null}

        {errorMessage ? (
          <p className="text-xs text-red-600">{errorMessage}</p>
        ) : null}

        {status === "done" ? (
          <p className="text-xs text-emerald-600">Complete! Refreshing...</p>
        ) : null}
      </div>
    );
  }

  return (
    <Button onClick={startStream} variant="outline" size="sm" className="mt-3">
      <Sparkles className="size-3 mr-1" aria-hidden />
      {label ?? `Stream ${stage}`}
    </Button>
  );
}
