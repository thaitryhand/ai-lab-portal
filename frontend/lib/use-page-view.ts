"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

/**
 * React hook that automatically tracks page views on public pages.
 *
 * - Generates a session ID (stored in sessionStorage, persists for tab lifetime).
 * - Throttles to max 1 request per path per session per 30 seconds.
 * - Only tracks public pages (not /admin/* routes).
 * - Sends POST /api/page-view with path, referrer, session_id, viewport.
 */
export function usePageView() {
  const pathname = usePathname();
  const sessionIdRef = useRef<string>("");
  const lastTrackedRef = useRef<Map<string, number>>(new Map());

  // Initialize session ID once
  useEffect(() => {
    if (typeof window === "undefined") return;
    let sid = sessionStorage.getItem("pv_session_id");
    if (!sid) {
      sid = crypto.randomUUID();
      sessionStorage.setItem("pv_session_id", sid);
    }
    sessionIdRef.current = sid;
  }, []);

  // Track on pathname change
  useEffect(() => {
    if (typeof window === "undefined") return;
    // Skip admin routes
    if (pathname.startsWith("/admin")) return;

    const sessionId = sessionIdRef.current;
    if (!sessionId) return;

    const now = Date.now();
    const key = `${sessionId}:${pathname}`;
    const lastTime = lastTrackedRef.current.get(key) ?? 0;

    // Throttle: 30 second window
    if (now - lastTime < 30_000) return;

    lastTrackedRef.current.set(key, now);

    // Cleanup old entries periodically
    if (lastTrackedRef.current.size > 200) {
      const cutoff = now - 60_000;
      for (const [k, t] of lastTrackedRef.current) {
        if (t < cutoff) lastTrackedRef.current.delete(k);
      }
    }

    const payload = {
      path: pathname,
      referrer: document.referrer || null,
      session_id: sessionId,
      viewport_width: window.innerWidth,
      viewport_height: window.innerHeight,
    };

    // Fire-and-forget — no need to await
    fetch("/api/page-view", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).catch(() => {
      // Silently fail — analytics should never break the page
    });
  }, [pathname]);
}

/**
 * Client component that mounts usePageView in the root layout.
 */
export function PageViewTracker() {
  usePageView();
  return null;
}
