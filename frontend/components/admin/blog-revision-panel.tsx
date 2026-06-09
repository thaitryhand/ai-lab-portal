"use client";

import { useCallback, useEffect, useState, useTransition } from "react";
import { Clock, History, RotateCcw, X } from "lucide-react";

type Revision = {
  id: string;
  post_id: string;
  revision_number: number;
  title: string;
  content_markdown: string;
  created_at: string;
};

type Props = {
  postId: string;
  open: boolean;
  onClose: () => void;
  onRestore: () => void;
};

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function BlogRevisionPanel({ postId, open, onClose, onRestore }: Props) {
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Revision | null>(null);
  const [restoring, setRestoring] = useState(false);

  const [, startTransition] = useTransition();

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    startTransition(() => { setLoading(true); });
    startTransition(() => { setError(null); });

    fetch(`/api/admin/blog-posts/${postId}/revisions`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json() as Promise<Revision[]>;
      })
      .then((data) => {
        if (cancelled) return;
        startTransition(() => { setRevisions(data); });
        if (data.length > 0) startTransition(() => { setSelected(data[0]); });
      })
      .catch((e) => {
        if (cancelled) return;
        startTransition(() => {
          setError(e instanceof Error ? e.message : "Failed to load revisions");
        });
      })
      .finally(() => {
        if (!cancelled) startTransition(() => { setLoading(false); });
      });

    return () => {
      cancelled = true;
    };
  }, [open, postId]);

  const handleRestore = useCallback(async () => {
    if (!selected) return;
    setRestoring(true);
    try {
      const res = await fetch(
        `/api/admin/blog-posts/${postId}/revisions/${selected.id}/restore`,
        { method: "POST" },
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      onRestore();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Restore failed");
    } finally {
      setRestoring(false);
    }
  }, [selected, postId, onRestore, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      {/* Panel */}
      <div className="relative ml-auto flex h-full w-full max-w-lg flex-col border-l bg-background shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <div>
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <History className="h-4 w-4" />
              Revision History
            </h2>
            <p className="text-sm text-muted-foreground">
              View and restore previous versions of this post.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 text-muted-foreground hover:bg-muted"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
              Loading revisions...
            </div>
          )}

          {error && (
            <div className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {!loading && !error && revisions.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
              <Clock className="mb-2 h-8 w-8 opacity-40" />
              <p className="text-sm">No revisions yet</p>
              <p className="text-xs">Revisions are saved automatically when you edit this post.</p>
            </div>
          )}

          {!loading && revisions.length > 0 && (
            <div className="space-y-4">
              {/* Revision list */}
              <div className="max-h-48 overflow-y-auto rounded-md border">
                {revisions.map((rev) => (
                  <button
                    key={rev.id}
                    type="button"
                    className={`flex w-full items-start gap-3 border-b px-4 py-3 text-left text-sm transition-colors last:border-0 hover:bg-muted/50 ${
                      selected?.id === rev.id ? "bg-muted" : ""
                    }`}
                    onClick={() => setSelected(rev)}
                  >
                    <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand/10 text-[10px] font-bold text-brand">
                      {rev.revision_number}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium">{rev.title}</p>
                      <p className="text-xs text-muted-foreground">{formatTime(rev.created_at)}</p>
                    </div>
                  </button>
                ))}
              </div>

              {/* Preview */}
              {selected && (
                <div className="rounded-md border">
                  <div className="border-b bg-muted/50 px-4 py-2 text-xs font-medium text-muted-foreground">
                    Revision {selected.revision_number} — {formatTime(selected.created_at)}
                  </div>
                  <div className="max-h-48 overflow-y-auto p-4 text-sm text-muted-foreground">
                    <div className="line-clamp-6">
                      {selected.content_markdown.slice(0, 500)}
                      {selected.content_markdown.length > 500 && "..."}
                    </div>
                  </div>
                </div>
              )}

              {/* Restore button */}
              {selected && (
                <button
                  type="button"
                  className="flex w-full items-center justify-center gap-2 rounded-md border px-4 py-2 text-sm font-medium transition-colors hover:bg-muted/50 disabled:opacity-50"
                  onClick={handleRestore}
                  disabled={restoring}
                >
                  <RotateCcw className={`h-3.5 w-3.5 ${restoring ? "animate-spin" : ""}`} />
                  {restoring ? "Restoring..." : `Restore revision ${selected.revision_number}`}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
