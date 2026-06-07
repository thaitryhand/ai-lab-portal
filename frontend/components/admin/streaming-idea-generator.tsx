"use client";

import { useCallback, useRef, useState } from "react";
import { Loader2, Sparkles, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type Status = "idle" | "connecting" | "streaming" | "done" | "error";

type Props = {
  /** Project context fields sent to the generation endpoint. */
  payload: {
    project_name: string;
    project_summary: string;
    ai_capabilities: string;
    technical_highlights: string;
    business_value: string;
  };
  /** The label for the source picker (e.g. "Project" or "Showcase"). */
  sourceLabel?: string;
};

export function StreamingIdeaGenerator({ payload, sourceLabel = "context" }: Props) {
  const router = useRouter();
  const [status, setStatus] = useState<Status>("idle");
  const [tokens, setTokens] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort();
      abortRef.current = null;
    }
    setStatus("idle");
    setTokens([]);
    setErrorMessage(null);
  }, []);

  const startGeneration = useCallback(async () => {
    reset();
    setStatus("connecting");

    try {
      const controller = new AbortController();
      abortRef.current = controller;

      const response = await fetch("/api/admin/blog-ideas/generate-stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errBody = await response.json().catch(() => ({ error: response.statusText }));
        setErrorMessage(errBody.error ?? `HTTP ${response.status}`);
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

        // Parse SSE events: "data: {json}\n\n"
        const lines = buffer.split("\n");
        // Keep the last potentially incomplete line in the buffer
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

              case "result":
                // Contains the raw generated idea (before saving)
                break;

              case "saved":
                setStatus("done");
                // Redirect to the new idea's detail page
                if (event.redirect_url) {
                  router.push(event.redirect_url);
                }
                return;

              case "error":
                setErrorMessage(event.data ?? "Generation failed");
                setStatus("error");
                return;

              case "status":
                // Lifecycle update — ignore for now
                break;
            }
          } catch {
            // Skip malformed JSON events
          }
        }
      }

      // Stream ended without a 'saved' event
      setStatus("done");
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setStatus("idle");
        return;
      }
      setErrorMessage(err instanceof Error ? err.message : "Unknown error");
      setStatus("error");
    }
  }, [payload, reset, router]);

  const isActive = status === "connecting" || status === "streaming";

  return (
    <div className="space-y-3">
      {/* Controls */}
      <div className="flex items-center gap-2">
        {status === "idle" || status === "done" ? (
          <Button onClick={startGeneration} variant="brand" disabled={isActive}>
            <Sparkles className="size-4" aria-hidden />
            Stream-generate idea
          </Button>
        ) : null}

        {status === "connecting" ? (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Connecting...
          </div>
        ) : null}

        {status === "error" ? (
          <Button onClick={reset} variant="outline" size="sm">
            Retry
          </Button>
        ) : null}

        {isActive ? (
          <Button
            onClick={() => {
              if (abortRef.current) abortRef.current.abort();
            }}
            variant="outline"
            size="sm"
          >
            <XCircle className="size-4 mr-1" aria-hidden />
            Stop
          </Button>
        ) : null}
      </div>

      {/* Progress indicator */}
      {isActive ? (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="inline-block size-2 rounded-full bg-brand animate-pulse" />
          Generating from {sourceLabel}...
        </div>
      ) : null}

      {/* Token display */}
      {tokens.length > 0 ? (
        <div
          className={cn(
            "max-h-60 overflow-y-auto rounded-lg border border-border/70 bg-muted/30 p-4",
            "text-sm leading-relaxed text-foreground whitespace-pre-wrap",
          )}
        >
          {tokens.join("")}
          {isActive ? (
            <span className="inline-block w-1.5 h-4 ml-0.5 bg-brand animate-pulse" />
          ) : null}
        </div>
      ) : null}

      {/* Error */}
      {errorMessage ? (
        <p className="text-sm text-red-600 dark:text-red-400">{errorMessage}</p>
      ) : null}

      {/* Done */}
      {status === "done" && tokens.length === 0 ? (
        <p className="text-sm text-muted-foreground">Generation complete. Redirecting...</p>
      ) : null}
    </div>
  );
}
