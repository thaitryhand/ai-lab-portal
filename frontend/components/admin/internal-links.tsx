"use client";

import { useCallback, useEffect, useState } from "react";
import { ExternalLink, Lightbulb, Loader2 } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

type Suggestion = {
  title: string;
  slug: string;
  reason: string;
};

type Props = {
  ideaId: string;
  /** Only show when draft exists */
  enabled: boolean;
};

export function InternalLinks({ ideaId, enabled }: Props) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLinks = useCallback(async () => {
    if (!enabled) return;
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/admin/blog-ideas/${ideaId}/suggest-links`,
      );
      if (!response.ok) {
        setError(`HTTP ${response.status}`);
        return;
      }
      const data: Suggestion[] = await response.json();
      setSuggestions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, [ideaId, enabled]);

  useEffect(() => {
    if (enabled && suggestions.length === 0 && !loading) {
      // Defer via microtask to satisfy React Compiler set-state-in-effect rule
      queueMicrotask(() => fetchLinks());
    }
  }, [enabled, fetchLinks, loading, suggestions.length]);

  if (!enabled) return null;

  return (
    <div className="rounded-lg border border-border/60 bg-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <Lightbulb className="size-4 text-amber-500" aria-hidden />
        <h3 className="text-sm font-semibold">Suggested internal links</h3>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Loader2 className="size-3 animate-spin" />
          Analyzing draft...
        </div>
      ) : error ? (
        <p className="text-xs text-red-600">{error}</p>
      ) : suggestions.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          No related posts found. Link suggestions appear when published posts
          share keywords with this draft.
        </p>
      ) : (
        <ul className="space-y-2">
          {suggestions.map((s) => (
            <li key={s.slug}>
              <Link
                href={`/blog/${s.slug}`}
                target="_blank"
                className={cn(
                  "flex items-start gap-2 rounded-md border border-border/40 p-2.5",
                  "transition-colors hover:bg-muted/50 text-sm",
                )}
              >
                <ExternalLink className="size-3.5 mt-0.5 shrink-0 text-muted-foreground" />
                <div className="min-w-0">
                  <p className="font-medium truncate">{s.title}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {s.reason}
                  </p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
