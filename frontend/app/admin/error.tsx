"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";

export default function AdminError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  void error;

  return (
    <div className="flex min-h-dvh flex-col items-center justify-center gap-6 bg-background px-4">
      <span className="flex size-14 items-center justify-center rounded-full bg-red-500/10 ring-1 ring-red-500/20">
        <AlertTriangle className="size-7 text-red-500" aria-hidden />
      </span>
      <div className="space-y-2 text-center">
        <h1 className="text-xl font-semibold text-foreground">Something went wrong</h1>
        <p className="mx-auto max-w-sm text-sm leading-relaxed text-muted-foreground">
          The admin panel encountered an unexpected error. This might be a temporary issue — try again, or sign out and back in.
        </p>
      </div>
      <div className="flex gap-3">
        <button
          type="button"
          onClick={reset}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground shadow-sm transition-colors hover:bg-primary/90"
        >
          <RefreshCw className="size-4" />
          Try again
        </button>
      </div>
      <p className="text-xs text-muted-foreground/60">
        Error digest: {error.digest ?? "N/A"}
      </p>
    </div>
  );
}
