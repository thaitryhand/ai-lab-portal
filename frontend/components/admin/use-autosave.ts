"use client";

import { useCallback, useEffect, useRef, useState, useTransition } from "react";

type SaveStatus = "saved" | "saving" | "unsaved" | "error";

type UseAutosaveOptions = {
  postId: string | undefined;
  content: string;
  title: string;
  slug: string;
  saveAction: (formData: FormData) => Promise<void>;
  /** Debounce delay for server save in ms (default 3000). */
  serverDelay?: number;
  /** Debounce delay for localStorage backup in ms (default 1000). */
  localDelay?: number;
};

type UseAutosaveReturn = {
  /** Current save status indicator. */
  saveStatus: SaveStatus;
  /** True if there are unsaved changes. */
  isDirty: boolean;
  /** Manually trigger a save. */
  save: () => Promise<void>;
  /** Whether a local (unsaved) draft exists from a previous session. */
  hasLocalDraft: boolean;
  /** The local draft data if available. */
  localDraft: { content: string; title: string; slug: string; savedAt: number } | null;
  /** Restore the local draft into the editor. */
  restoreFromLocal: () => void;
  /** Clear the local draft from storage. */
  clearLocalDraft: () => void;
};

const STORAGE_PREFIX = "autosave:blog:";

function storageKey(postId: string | undefined): string {
  return `${STORAGE_PREFIX}${postId || "new"}`;
}

function getLocalDraft(postId: string | undefined): {
  content: string;
  title: string;
  slug: string;
  savedAt: number;
} | null {
  try {
    const raw = localStorage.getItem(storageKey(postId));
    if (raw) return JSON.parse(raw);
  } catch {
    // ignore
  }
  return null;
}

export function useAutosave({
  postId,
  content,
  title,
  slug,
  saveAction,
  serverDelay = 3000,
  localDelay = 1000,
}: UseAutosaveOptions): UseAutosaveReturn {
  const [, startTransition] = useTransition();
  const [saveStatus, setSaveStatus] = useState<SaveStatus>(postId ? "saved" : "unsaved");
  const [isDirty, setIsDirty] = useState(false);
  const [hasLocalDraft, setHasLocalDraft] = useState(() => {
    if (typeof window === "undefined") return false;
    return getLocalDraft(postId) !== null;
  });
  const [localDraft, setLocalDraft] = useState<UseAutosaveReturn["localDraft"]>(() => {
    if (typeof window === "undefined") return null;
    return getLocalDraft(postId);
  });

  const serverTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const localTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const contentRef = useRef(content);
  const titleRef = useRef(title);
  const slugRef = useRef(slug);
  const saveActionRef = useRef(saveAction);

  // Sync refs — allowed in useEffect (side effect, not render)
  useEffect(() => {
    contentRef.current = content;
    titleRef.current = title;
    slugRef.current = slug;
    saveActionRef.current = saveAction;
  }, [content, title, slug, saveAction]);

  // Track previous content/title to detect changes via refs instead of direct comparison
  const prevContentRef = useRef(content);
  const prevTitleRef = useRef(title);

  // Mark as unsaved when content or title changes
  useEffect(() => {
    if (!postId) return;
    const contentChanged = content !== prevContentRef.current;
    const titleChanged = title !== prevTitleRef.current;
    prevContentRef.current = content;
    prevTitleRef.current = title;

    if (contentChanged || titleChanged) {
      startTransition(() => {
        setSaveStatus("unsaved");
      });
      setIsDirty(true);
    }
  }, [content, title, postId, startTransition]);

  // localStorage backup (debounced)
  useEffect(() => {
    if (localTimerRef.current) clearTimeout(localTimerRef.current);
    localTimerRef.current = setTimeout(() => {
      try {
        localStorage.setItem(
          storageKey(postId),
          JSON.stringify({ content, title, slug, savedAt: Date.now() }),
        );
      } catch {
        // localStorage full or unavailable
      }
    }, localDelay);
    return () => {
      if (localTimerRef.current) clearTimeout(localTimerRef.current);
    };
  }, [content, title, slug, postId, localDelay]);

  // Server autosave (debounced)
  useEffect(() => {
    if (!postId) return;
    if (serverTimerRef.current) clearTimeout(serverTimerRef.current);
    serverTimerRef.current = setTimeout(async () => {
      startTransition(() => {
        setSaveStatus("saving");
      });
      try {
        const fd = new FormData();
        fd.set("contentMarkdown", contentRef.current);
        fd.set("title", titleRef.current);
        fd.set("slug", slugRef.current);
        fd.set("excerpt", "");
        fd.set("authorName", "");
        await saveActionRef.current(fd);
        startTransition(() => {
          setSaveStatus("saved");
        });
        setIsDirty(false);
        // Clear localStorage after successful save
        try {
          localStorage.removeItem(storageKey(postId));
        } catch {
          // ignore
        }
        setHasLocalDraft(false);
        setLocalDraft(null);
      } catch {
        startTransition(() => {
          setSaveStatus("error");
        });
      }
    }, serverDelay);
    return () => {
      if (serverTimerRef.current) clearTimeout(serverTimerRef.current);
    };
  }, [content, title, slug, postId, serverDelay, startTransition]);

  const save = useCallback(async () => {
    if (!postId) return;
    startTransition(() => {
      setSaveStatus("saving");
    });
    try {
      const fd = new FormData();
      fd.set("contentMarkdown", contentRef.current);
      fd.set("title", titleRef.current);
      fd.set("slug", slugRef.current);
      fd.set("excerpt", "");
      fd.set("authorName", "");
      await saveActionRef.current(fd);
      startTransition(() => {
        setSaveStatus("saved");
      });
      setIsDirty(false);
    } catch {
      startTransition(() => {
        setSaveStatus("error");
      });
    }
  }, [postId, startTransition]);

  const restoreFromLocal = useCallback(() => {
    // Re-read from localStorage in case it changed
    const draft = getLocalDraft(postId);
    if (draft) {
      contentRef.current = draft.content;
      titleRef.current = draft.title;
      slugRef.current = draft.slug;
    }
  }, [postId]);

  const clearLocalDraft = useCallback(() => {
    try {
      localStorage.removeItem(storageKey(postId));
    } catch {
      // ignore
    }
    setHasLocalDraft(false);
    setLocalDraft(null);
  }, [postId]);

  return {
    saveStatus,
    isDirty,
    save,
    hasLocalDraft,
    localDraft,
    restoreFromLocal,
    clearLocalDraft,
  };
}
