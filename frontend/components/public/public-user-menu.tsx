"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { Bookmark, FileEdit, LogOut, Moon, Sun, User } from "lucide-react";

import { NotificationBell } from "@/components/public/notification-bell";
import { useSession } from "@/components/session-provider";
import { cn } from "@/lib/utils";

function AvatarFallback({
  name,
  size = "sm",
}: {
  name: string;
  size?: "sm" | "md";
}) {
  const initial = name?.charAt(0)?.toUpperCase() ?? "?";
  return (
    <span
      className={cn(
        "flex items-center justify-center rounded-full bg-linear-to-br from-brand/80 to-brand text-brand-foreground font-semibold select-none",
        size === "sm" && "h-8 w-8 text-sm",
        size === "md" && "h-10 w-10 text-base",
      )}
      aria-hidden
    >
      {initial}
    </span>
  );
}

export function PublicUserMenu() {
  const router = useRouter();
  const { session, loading, avatarUrl, refresh } = useSession();
  const [open, setOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    if (typeof document === "undefined") return "light";
    return document.documentElement.classList.contains("dark")
      ? "dark"
      : "light";
  });
  const menuRef = useRef<HTMLDivElement>(null);

  // Detect theme (local, no server round-trip)
  useEffect(() => {
    const html = document.documentElement;
    const observer = new MutationObserver(() => {
      setTheme(html.classList.contains("dark") ? "dark" : "light");
    });
    observer.observe(html, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  // Close menu on outside click
  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  async function handleSignOut() {
    setOpen(false);
    try {
      const response = await fetch("/api/auth/sign-out", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!response.ok) return;
      await refresh();
      router.refresh();
    } catch {
      // ignore
    }
  }

  function toggleTheme() {
    const html = document.documentElement;
    const next = theme === "light" ? "dark" : "light";
    html.classList.toggle("dark", next === "dark");
    setTheme(next);
  }

  // ── First fetch still in-flight ──────────────────────────────────────────
  // Render invisible placeholders with the exact same dimensions as the
  // logged-out UI so the layout is stable from paint 1. No skeleton pulse,
  // no spinner, no layout shift when the fetch completes.
  if (loading && !session) {
    return (
      <div className="invisible flex items-center gap-1.5" aria-hidden>
        <div className="flex h-10 w-10 items-center justify-center rounded-full">
          <Moon className="size-4" />
        </div>
        <div className="hidden h-10 w-17 rounded-full sm:block" />
        <div className="h-10 w-28 rounded-full" />
      </div>
    );
  }

  // ── Confirmed: not logged in ─────────────────────────────────────────────
  if (!session) {
    return (
      <div className="flex items-center gap-1.5">
        <button
          type="button"
          onClick={toggleTheme}
          className="flex h-10 w-10 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
        >
          {theme === "light" ? (
            <Moon className="size-4" />
          ) : (
            <Sun className="size-4" />
          )}
        </button>
        <Link
          href="/login"
          className="hidden sm:inline-flex items-center justify-center rounded-full px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          Sign in
        </Link>
        <Link
          href="/register"
          className="inline-flex items-center justify-center rounded-full bg-brand px-3 py-2 text-sm font-medium text-brand-foreground transition-all hover:opacity-90"
        >
          Create account
        </Link>
      </div>
    );
  }

  // ── Confirmed: logged in ─────────────────────────────────────────────────
  const userName = session.user.name || session.user.email || "User";
  const userImage = avatarUrl;

  return (
    <div ref={menuRef} className="relative flex items-center gap-1.5">
      {/* Write a post */}
      <Link
        href="/blog/new"
        className="hidden sm:inline-flex items-center gap-1.5 rounded-full border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted hover:border-brand/30"
      >
        <FileEdit className="size-3.5" />
        <span>Write a post</span>
      </Link>

      {/* Notifications */}
      <NotificationBell />

      {/* Theme toggle */}
      <button
        type="button"
        onClick={toggleTheme}
        className="flex h-10 w-10 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
      >
        {theme === "light" ? (
          <Moon className="size-4" />
        ) : (
          <Sun className="size-4" />
        )}
      </button>

      {/* Avatar trigger */}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="relative flex items-center gap-2 rounded-full transition-colors hover:opacity-80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        aria-expanded={open}
        aria-haspopup="true"
        aria-label="User menu"
      >
        {userImage ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={userImage}
            alt=""
            className="h-10 w-10 rounded-full object-cover ring-2 ring-border"
          />
        ) : (
          <AvatarFallback name={userName} size="md" />
        )}
      </button>

      {/* Dropdown */}
      {open && (
        <div
          className="absolute right-0 top-full z-50 mt-2 min-w-55 overflow-hidden rounded-xl border border-border bg-card shadow-lg"
          role="menu"
        >
          {/* User info */}
          <div className="border-b border-border px-4 py-3">
            <p className="truncate text-sm font-medium text-foreground">
              {userName}
            </p>
            <p className="truncate text-xs text-muted-foreground">
              {session.user.email}
            </p>
          </div>

          <div className="p-1.5">
            <Link
              href="/profile"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground transition-colors hover:bg-muted"
              role="menuitem"
            >
              <User className="size-4 text-muted-foreground" />
              Profile
            </Link>
            <Link
              href="/bookmarks"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground transition-colors hover:bg-muted"
              role="menuitem"
            >
              <Bookmark className="size-4 text-muted-foreground" />
              Bookmarks
            </Link>
            <Link
              href="/blog/new"
              onClick={() => setOpen(false)}
              className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground transition-colors hover:bg-muted sm:hidden"
              role="menuitem"
            >
              <FileEdit className="size-4 text-muted-foreground" />
              Write a post
            </Link>
          </div>

          <div className="border-t border-border p-1.5">
            <button
              type="button"
              onClick={handleSignOut}
              className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-foreground transition-colors hover:bg-muted"
              role="menuitem"
            >
              <LogOut className="size-4 text-muted-foreground" />
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
