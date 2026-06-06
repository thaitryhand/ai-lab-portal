"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, startTransition } from "react";
import { Bookmark } from "lucide-react";

import { cn } from "@/lib/utils";

type PublicBookmarkButtonProps = {
  slug: string;
};

export function PublicBookmarkButton({ slug }: PublicBookmarkButtonProps) {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [isBookmarked, setIsBookmarked] = useState(false);

  useEffect(() => {
    fetch("/api/auth/get-session")
      .then((r) => r.json())
      .then((data) => {
        setIsAuthenticated(!!data?.user);
        if (data?.user) {
          // Check bookmark status
          fetch(`/api/bookmarks/check/${slug}`)
            .then((r) => r.json())
            .then((bData) => setIsBookmarked(!!bData))
            .catch(() => {});
        }
      })
      .catch(() => setIsAuthenticated(false));
  }, [slug]);

  const handleToggle = useCallback(async () => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    startTransition(async () => {
      setIsBookmarked((prev) => !prev);
      try {
        const res = await fetch(`/api/bookmarks/toggle/${slug}`, {
          method: "POST",
        });
        if (!res.ok) {
          setIsBookmarked((prev) => !prev); // revert
        }
      } catch {
        setIsBookmarked((prev) => !prev); // revert
      }
    });
  }, [isAuthenticated, slug, router]);

  if (isAuthenticated === null) {
    return (
      <span className="flex h-9 w-9 items-center justify-center">
        <span className="size-4 rounded bg-muted animate-pulse" />
      </span>
    );
  }

  return (
    <button
      type="button"
      onClick={handleToggle}
      className={cn(
        "flex h-9 w-9 items-center justify-center rounded-full transition-colors",
        isBookmarked
          ? "text-brand hover:bg-brand/10"
          : "text-muted-foreground hover:bg-muted hover:text-foreground",
      )}
      aria-label={isBookmarked ? "Remove bookmark" : "Bookmark this post"}
    >
      <Bookmark className={cn("size-4", isBookmarked && "fill-current")} />
    </button>
  );
}
